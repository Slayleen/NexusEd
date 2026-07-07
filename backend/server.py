from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Annotated

from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, BeforeValidator
from bson import ObjectId

from emergentintegrations.llm.chat import LlmChat, UserMessage

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PyObjectId = Annotated[str, BeforeValidator(str)]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "type": "access",
               "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def clean(doc: dict) -> dict:
    if not doc:
        return doc
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("password_hash", None)
    return doc

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str
    school: Optional[str] = ""
    grade: Optional[str] = ""

class LoginInput(BaseModel):
    email: str
    password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    interests: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    looking_for: Optional[List[str]] = None

class ProjectInput(BaseModel):
    title: str
    description: str
    category: str
    roles_needed: List[str] = []
    skills: List[str] = []
    timeline: Optional[str] = ""

class OpportunityInput(BaseModel):
    title: str
    org: str
    type: str
    description: str
    deadline: Optional[str] = ""
    tags: List[str] = []
    link: Optional[str] = ""

class MessageInput(BaseModel):
    to_user_id: str
    text: str

class ForumPostInput(BaseModel):
    community: str
    title: str
    body: str

class ForumCommentInput(BaseModel):
    text: str

class MatchInput(BaseModel):
    goal: str

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return clean(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def set_auth_cookie(response: Response, token: str):
    response.set_cookie(key="access_token", value=token, httponly=True,
                        secure=True, samesite="none", max_age=604800, path="/")

@api_router.post("/auth/register")
async def register(data: RegisterInput, response: Response):
    email = data.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    doc = {
        "email": email, "password_hash": hash_password(data.password),
        "name": data.name, "school": data.school or "", "grade": data.grade or "",
        "bio": "", "avatar": f"https://api.dicebear.com/7.x/thumbs/svg?seed={data.name}",
        "interests": [], "skills": [], "looking_for": [],
        "verified": email.endswith(".edu"), "role": "student",
        "reputation": {"projects_completed": 0, "endorsements": 0, "reliability": 100},
        "created_at": now_iso(),
    }
    res = await db.users.insert_one(doc)
    uid = str(res.inserted_id)
    set_auth_cookie(response, create_access_token(uid, email))
    doc["_id"] = res.inserted_id
    return clean(doc)

@api_router.post("/auth/login")
async def login(data: LoginInput, response: Response):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_auth_cookie(response, create_access_token(str(user["_id"]), email))
    return clean(user)

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}

@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user

@api_router.put("/profile")
async def update_profile(data: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": updates})
    fresh = await db.users.find_one({"_id": ObjectId(user["id"])})
    return clean(fresh)

@api_router.get("/students")
async def list_students(user: dict = Depends(get_current_user)):
    students = await db.users.find({"role": "student"}).to_list(200)
    return [clean(s) for s in students if str(s["_id"]) != user["id"]]

@api_router.get("/students/{sid}")
async def get_student(sid: str, user: dict = Depends(get_current_user)):
    s = await db.users.find_one({"_id": ObjectId(sid)})
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    return clean(s)

@api_router.post("/students/{sid}/endorse")
async def endorse(sid: str, user: dict = Depends(get_current_user)):
    await db.users.update_one({"_id": ObjectId(sid)}, {"$inc": {"reputation.endorsements": 1}})
    s = await db.users.find_one({"_id": ObjectId(sid)})
    return clean(s)

def _local_match(goal, candidates):
    import re
    words = set(re.findall(r"[a-zA-Z\+#]+", goal.lower()))
    scored = []
    for c in candidates:
        tags = [t.lower() for t in (c["skills"] + c["interests"] + c["looking_for"])]
        hits = [t for t in tags if any((w in t or t in w) for w in words if len(w) > 2)]
        overlap = len(set(hits))
        bio_hit = any(w in c["bio"].lower() for w in words if len(w) > 3)
        score = min(96, 55 + overlap * 12 + (8 if bio_hit else 0))
        matched = list(dict.fromkeys(hits))[:3]
        if matched:
            reason = f"{c['name'].split()[0]} brings {', '.join(matched)} — directly relevant to your goal."
        else:
            reason = f"{c['name'].split()[0]} is an active, reliable collaborator worth reaching out to."
            score = 60
        scored.append({"id": c["id"], "reason": reason, "score": score, "_o": overlap})
    scored.sort(key=lambda x: x["_o"], reverse=True)
    top = scored[:5] if any(s["_o"] > 0 for s in scored) else scored[:4]
    for s in top:
        s.pop("_o", None)
    return top


@api_router.post("/match")
async def ai_match(data: MatchInput, user: dict = Depends(get_current_user)):
    import json
    students = await db.users.find({"role": "student"}).to_list(200)
    pool = [s for s in students if str(s["_id"]) != user["id"]]
    candidates = [{
        "id": str(s["_id"]), "name": s["name"], "grade": s.get("grade", ""),
        "school": s.get("school", ""), "skills": s.get("skills", []),
        "interests": s.get("interests", []), "looking_for": s.get("looking_for", []),
        "bio": s.get("bio", "")
    } for s in pool]

    system = (
        "You are Nexus AI, a matchmaking engine for ambitious high school students. "
        "Given a student's goal and a list of candidate students, pick the 3-5 BEST teammates. "
        "For each, write ONE short, specific sentence on why they fit the goal. "
        "Respond ONLY with valid JSON in this exact shape: "
        '{"matches":[{"id":"<candidate id>","reason":"<why they fit>","score":<0-100>}]}'
    )
    prompt = f"GOAL: {data.goal}\n\nCANDIDATES:\n{json.dumps(candidates)}"
    try:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"],
                       session_id=f"match-{user['id']}", system_message=system).with_model("openai", "gpt-5.4-mini")
        reply = await chat.send_message(UserMessage(text=prompt))
        text = (reply if isinstance(reply, str) else str(reply)).strip()
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "", 1).strip()
        parsed = json.loads(text)
        raw_matches = parsed.get("matches", [])
    except Exception as e:
        logger.error(f"AI match error: {e}")
        raw_matches = _local_match(data.goal, candidates)

    by_id = {str(s["_id"]): s for s in pool}
    results = []
    for m in raw_matches:
        s = by_id.get(m.get("id"))
        if s:
            results.append({"student": clean(s), "reason": m.get("reason", ""), "score": m.get("score", 70)})
    return {"matches": results}

@api_router.get("/projects")
async def list_projects(user: dict = Depends(get_current_user)):
    projects = await db.projects.find().sort("created_at", -1).to_list(200)
    out = []
    for p in projects:
        p = clean(p)
        owner = await db.users.find_one({"_id": ObjectId(p["owner_id"])})
        p["owner"] = {"id": str(owner["_id"]), "name": owner["name"], "avatar": owner.get("avatar")} if owner else None
        out.append(p)
    return out

@api_router.post("/projects")
async def create_project(data: ProjectInput, user: dict = Depends(get_current_user)):
    doc = data.model_dump()
    doc.update({"owner_id": user["id"], "members": [user["id"]], "applicants": [],
                "status": "active", "progress": 0, "created_at": now_iso()})
    res = await db.projects.insert_one(doc)
    doc["_id"] = res.inserted_id
    p = clean(doc)
    p["owner"] = {"id": user["id"], "name": user["name"], "avatar": user.get("avatar")}
    return p

@api_router.post("/projects/{pid}/join")
async def join_project(pid: str, user: dict = Depends(get_current_user)):
    await db.projects.update_one({"_id": ObjectId(pid)}, {"$addToSet": {"applicants": user["id"]}})
    return {"ok": True}

@api_router.post("/projects/{pid}/progress")
async def update_progress(pid: str, body: dict, user: dict = Depends(get_current_user)):
    prog = int(body.get("progress", 0))
    status = "completed" if prog >= 100 else "active"
    await db.projects.update_one({"_id": ObjectId(pid)}, {"$set": {"progress": prog, "status": status}})
    p = await db.projects.find_one({"_id": ObjectId(pid)})
    return clean(p)

@api_router.get("/opportunities")
async def list_opportunities(user: dict = Depends(get_current_user)):
    opps = await db.opportunities.find().sort("created_at", -1).to_list(200)
    return [clean(o) for o in opps]

@api_router.post("/opportunities")
async def create_opportunity(data: OpportunityInput, user: dict = Depends(get_current_user)):
    doc = data.model_dump()
    doc.update({"posted_by": user["id"], "created_at": now_iso()})
    res = await db.opportunities.insert_one(doc)
    doc["_id"] = res.inserted_id
    return clean(doc)

@api_router.get("/conversations")
async def conversations(user: dict = Depends(get_current_user)):
    msgs = await db.messages.find({"$or": [{"from_user_id": user["id"]}, {"to_user_id": user["id"]}]}).sort("created_at", -1).to_list(1000)
    partners = {}
    for m in msgs:
        other = m["to_user_id"] if m["from_user_id"] == user["id"] else m["from_user_id"]
        if other not in partners:
            partners[other] = m
    out = []
    for pid, last in partners.items():
        u = await db.users.find_one({"_id": ObjectId(pid)})
        if u:
            out.append({"user": {"id": str(u["_id"]), "name": u["name"], "avatar": u.get("avatar")},
                        "last_message": last["text"], "last_at": last["created_at"]})
    return out

@api_router.get("/messages/{other_id}")
async def get_messages(other_id: str, user: dict = Depends(get_current_user)):
    msgs = await db.messages.find({"$or": [
        {"from_user_id": user["id"], "to_user_id": other_id},
        {"from_user_id": other_id, "to_user_id": user["id"]}]}).sort("created_at", 1).to_list(1000)
    return [clean(m) for m in msgs]

@api_router.post("/messages")
async def post_message(data: MessageInput, user: dict = Depends(get_current_user)):
    doc = {"from_user_id": user["id"], "to_user_id": data.to_user_id,
           "text": data.text, "created_at": now_iso()}
    res = await db.messages.insert_one(doc)
    doc["_id"] = res.inserted_id
    return clean(doc)

@api_router.get("/forum")
async def list_forum(community: Optional[str] = None, user: dict = Depends(get_current_user)):
    q = {"community": community} if community else {}
    posts = await db.forum_posts.find(q).sort("created_at", -1).to_list(200)
    out = []
    for p in posts:
        p = clean(p)
        author = await db.users.find_one({"_id": ObjectId(p["author_id"])})
        p["author"] = {"id": str(author["_id"]), "name": author["name"], "avatar": author.get("avatar")} if author else None
        p["comment_count"] = await db.forum_comments.count_documents({"post_id": p["id"]})
        out.append(p)
    return out

@api_router.post("/forum")
async def create_post(data: ForumPostInput, user: dict = Depends(get_current_user)):
    doc = data.model_dump()
    doc.update({"author_id": user["id"], "upvotes": 0, "created_at": now_iso()})
    res = await db.forum_posts.insert_one(doc)
    doc["_id"] = res.inserted_id
    p = clean(doc)
    p["author"] = {"id": user["id"], "name": user["name"], "avatar": user.get("avatar")}
    p["comment_count"] = 0
    return p

@api_router.get("/forum/{pid}/comments")
async def get_comments(pid: str, user: dict = Depends(get_current_user)):
    comments = await db.forum_comments.find({"post_id": pid}).sort("created_at", 1).to_list(500)
    out = []
    for c in comments:
        c = clean(c)
        author = await db.users.find_one({"_id": ObjectId(c["author_id"])})
        c["author"] = {"id": str(author["_id"]), "name": author["name"], "avatar": author.get("avatar")} if author else None
        out.append(c)
    return out

@api_router.post("/forum/{pid}/comments")
async def add_comment(pid: str, data: ForumCommentInput, user: dict = Depends(get_current_user)):
    doc = {"post_id": pid, "author_id": user["id"], "text": data.text, "created_at": now_iso()}
    res = await db.forum_comments.insert_one(doc)
    doc["_id"] = res.inserted_id
    c = clean(doc)
    c["author"] = {"id": user["id"], "name": user["name"], "avatar": user.get("avatar")}
    return c

@api_router.post("/forum/{pid}/upvote")
async def upvote(pid: str, user: dict = Depends(get_current_user)):
    await db.forum_posts.update_one({"_id": ObjectId(pid)}, {"$inc": {"upvotes": 1}})
    return {"ok": True}

@api_router.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    my_projects = await db.projects.find({"members": user["id"]}).to_list(50)
    opps = await db.opportunities.find().sort("created_at", -1).to_list(4)
    students = await db.users.find({"role": "student"}).to_list(50)
    suggested = [clean(s) for s in students if str(s["_id"]) != user["id"]][:4]
    return {
        "my_projects": [clean(p) for p in my_projects],
        "opportunities": [clean(o) for o in opps],
        "suggested_teammates": suggested,
        "stats": {
            "projects": len(my_projects),
            "students": len(students),
            "opportunities": await db.opportunities.count_documents({}),
        }
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await seed()

@app.on_event("shutdown")
async def shutdown():
    client.close()

async def seed():
    from seed_data import STUDENTS, PROJECTS, OPPORTUNITIES, FORUM
    if await db.users.count_documents({"role": "student"}) > 0:
        return
    logger.info("Seeding demo data...")
    id_map = {}
    for s in STUDENTS:
        doc = {
            "email": s["email"], "password_hash": hash_password("password123"),
            "name": s["name"], "school": s["school"], "grade": s["grade"],
            "bio": s["bio"], "avatar": f"https://api.dicebear.com/7.x/thumbs/svg?seed={s['name'].replace(' ','')}",
            "interests": s["interests"], "skills": s["skills"], "looking_for": s["looking_for"],
            "verified": True, "role": "student",
            "reputation": s["reputation"], "created_at": now_iso(),
        }
        res = await db.users.insert_one(doc)
        id_map[s["name"]] = str(res.inserted_id)

    for p in PROJECTS:
        owner = id_map[p["owner"]]
        await db.projects.insert_one({
            "title": p["title"], "description": p["description"], "category": p["category"],
            "roles_needed": p["roles_needed"], "skills": p["skills"], "timeline": p["timeline"],
            "owner_id": owner, "members": [owner], "applicants": [],
            "status": p["status"], "progress": p["progress"], "created_at": now_iso(),
        })

    for o in OPPORTUNITIES:
        await db.opportunities.insert_one({**o, "posted_by": None, "created_at": now_iso()})

    for f in FORUM:
        author = id_map[f["author"]]
        res = await db.forum_posts.insert_one({
            "community": f["community"], "title": f["title"], "body": f["body"],
            "author_id": author, "upvotes": f["upvotes"], "created_at": now_iso(),
        })
        for c in f.get("comments", []):
            await db.forum_comments.insert_one({
                "post_id": str(res.inserted_id), "author_id": id_map[c["author"]],
                "text": c["text"], "created_at": now_iso(),
            })
    logger.info("Seeding complete.")
