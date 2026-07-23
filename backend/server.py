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

from groq import AsyncGroq

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

async def user_map(ids):
    oids = []
    for i in set(ids):
        try:
            oids.append(ObjectId(i))
        except Exception:
            pass
    if not oids:
        return {}
    docs = await db.users.find({"_id": {"$in": oids}}, {"name": 1, "avatar": 1}).to_list(len(oids))
    return {str(d["_id"]): {"id": str(d["_id"]), "name": d.get("name"), "avatar": d.get("avatar")} for d in docs}

async def shared_project_user_ids(uid: str) -> set:
    """User ids that share at least one project (as members) with the given user."""
    projects = await db.projects.find({"members": uid}).to_list(200)
    ids = set()
    for p in projects:
        for m in p.get("members", []):
            if m and m != uid:
                ids.add(m)
    return ids

async def my_connection_map(uid: str) -> dict:
    """Map other_user_id -> status relative to `uid`: connected / pending_out / pending_in."""
    conns = await db.connections.find({"$or": [{"requester_id": uid}, {"recipient_id": uid}]}).to_list(2000)
    out = {}
    for c in conns:
        other = c["recipient_id"] if c["requester_id"] == uid else c["requester_id"]
        if c["status"] == "accepted":
            out[other] = "connected"
        elif c["requester_id"] == uid:
            out[other] = "pending_out"
        else:
            out[other] = "pending_in"
    return out

async def are_connected(a: str, b: str) -> bool:
    c = await db.connections.find_one({"status": "accepted", "$or": [
        {"requester_id": a, "recipient_id": b},
        {"requester_id": b, "recipient_id": a},
    ]})
    return bool(c)

async def recompute_reputation(uid: str):
    reviews = await db.reviews.find({"reviewee_id": uid}).to_list(2000)
    if reviews:
        reliability = round(sum(r["reliability"] for r in reviews) / len(reviews))
        avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    else:
        reliability = 100
        avg_rating = 0
    await db.users.update_one({"_id": ObjectId(uid)}, {"$set": {
        "reputation.reliability": reliability,
        "reputation.avg_rating": avg_rating,
        "reputation.review_count": len(reviews),
    }})

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
    location: Optional[str] = None

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
    location: Optional[str] = "Remote"

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

class ReviewInput(BaseModel):
    rating: int              # 1-5
    reliability: int         # 0-100
    comment: str = ""
    project_id: Optional[str] = None

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
        "interests": [], "skills": [], "looking_for": [], "location": "",
        "verified": email.endswith(".edu"), "role": "student",
        "reputation": {"projects_completed": 0, "reliability": 100, "avg_rating": 0, "review_count": 0},
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
    shared = await shared_project_user_ids(user["id"])
    conn_map = await my_connection_map(user["id"])
    out = []
    for s in students:
        sid = str(s["_id"])
        if sid == user["id"]:
            continue
        c = clean(s)
        status = conn_map.get(sid, "none")
        c["can_review"] = (sid in shared) or (status == "connected")
        c["connection_status"] = status
        out.append(c)
    return out

@api_router.get("/students/{sid}")
async def get_student(sid: str, user: dict = Depends(get_current_user)):
    s = await db.users.find_one({"_id": ObjectId(sid)})
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    c = clean(s)
    shared = await shared_project_user_ids(user["id"])
    conn_map = await my_connection_map(user["id"])
    status = conn_map.get(sid, "none")
    c["can_review"] = (sid in shared) or (status == "connected")
    c["connection_status"] = status
    return c

@api_router.get("/students/{sid}/reviews")
async def list_reviews(sid: str, user: dict = Depends(get_current_user)):
    reviews = await db.reviews.find({"reviewee_id": sid}).sort("created_at", -1).to_list(500)
    umap = await user_map([r["reviewer_id"] for r in reviews])
    out = []
    for r in reviews:
        r = clean(r)
        r["reviewer"] = umap.get(r["reviewer_id"])
        out.append(r)
    return out

@api_router.post("/students/{sid}/reviews")
async def create_review(sid: str, data: ReviewInput, user: dict = Depends(get_current_user)):
    if sid == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot review yourself")
    target = await db.users.find_one({"_id": ObjectId(sid)})
    if not target:
        raise HTTPException(status_code=404, detail="Student not found")
    shared = await shared_project_user_ids(user["id"])
    connected = await are_connected(user["id"], sid)
    if sid not in shared and not connected:
        raise HTTPException(status_code=403, detail="You can only review students you've collaborated with on a project or are connected with")
    rating = max(1, min(5, int(data.rating)))
    reliability = max(0, min(100, int(data.reliability)))
    doc = {
        "reviewer_id": user["id"], "reviewee_id": sid,
        "project_id": data.project_id, "rating": rating,
        "reliability": reliability, "comment": (data.comment or "").strip(),
        "reviewer_name": user["name"], "reviewer_avatar": user.get("avatar"),
        "created_at": now_iso(),
    }
    # one review per reviewer -> reviewee (upsert = editable)
    await db.reviews.update_one(
        {"reviewer_id": user["id"], "reviewee_id": sid},
        {"$set": doc}, upsert=True,
    )
    await recompute_reputation(sid)
    fresh = await db.users.find_one({"_id": ObjectId(sid)})
    return clean(fresh)

@api_router.post("/connections/{sid}")
async def send_connection(sid: str, user: dict = Depends(get_current_user)):
    if sid == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot connect with yourself")
    if not await db.users.find_one({"_id": ObjectId(sid)}):
        raise HTTPException(status_code=404, detail="Student not found")
    existing = await db.connections.find_one({"$or": [
        {"requester_id": user["id"], "recipient_id": sid},
        {"requester_id": sid, "recipient_id": user["id"]},
    ]})
    if existing:
        # if the other person already requested me, accept it
        if existing["status"] == "pending" and existing["recipient_id"] == user["id"]:
            await db.connections.update_one({"_id": existing["_id"]},
                                            {"$set": {"status": "accepted", "updated_at": now_iso()}})
            return {"status": "connected"}
        return {"status": "connected" if existing["status"] == "accepted" else (
            "pending_out" if existing["requester_id"] == user["id"] else "pending_in")}
    await db.connections.insert_one({
        "requester_id": user["id"], "recipient_id": sid,
        "status": "pending", "created_at": now_iso(), "updated_at": now_iso(),
    })
    return {"status": "pending_out"}

@api_router.post("/connections/{sid}/respond")
async def respond_connection(sid: str, body: dict, user: dict = Depends(get_current_user)):
    action = body.get("action")
    conn = await db.connections.find_one({"requester_id": sid, "recipient_id": user["id"], "status": "pending"})
    if not conn:
        raise HTTPException(status_code=404, detail="No pending request from this student")
    if action == "accept":
        await db.connections.update_one({"_id": conn["_id"]},
                                        {"$set": {"status": "accepted", "updated_at": now_iso()}})
        return {"status": "connected"}
    await db.connections.delete_one({"_id": conn["_id"]})
    return {"status": "none"}

@api_router.get("/connections")
async def list_connections(user: dict = Depends(get_current_user)):
    conns = await db.connections.find({"status": "accepted", "$or": [
        {"requester_id": user["id"]}, {"recipient_id": user["id"]},
    ]}).to_list(1000)
    other_ids = [c["recipient_id"] if c["requester_id"] == user["id"] else c["requester_id"] for c in conns]
    oids = [ObjectId(i) for i in other_ids]
    docs = await db.users.find({"_id": {"$in": oids}}).to_list(len(oids)) if oids else []
    return [clean(d) for d in docs]

@api_router.get("/connections/requests")
async def list_requests(user: dict = Depends(get_current_user)):
    conns = await db.connections.find({"recipient_id": user["id"], "status": "pending"}).sort("created_at", -1).to_list(1000)
    umap = await user_map([c["requester_id"] for c in conns])
    out = []
    for c in conns:
        u = umap.get(c["requester_id"])
        if u:
            full = await db.users.find_one({"_id": ObjectId(c["requester_id"])})
            out.append(clean(full))
    return out

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
        groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
        completion = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        text = completion.choices[0].message.content.strip()
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
    umap = await user_map([p["owner_id"] for p in projects])
    conn_map = await my_connection_map(user["id"])
    out = []
    for p in projects:
        p = clean(p)
        owner = umap.get(p["owner_id"])
        if owner:
            owner = dict(owner)
            owner["connection_status"] = "self" if p["owner_id"] == user["id"] else conn_map.get(p["owner_id"], "none")
        p["owner"] = owner
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
    umap = await user_map(list(partners.keys()))
    out = []
    for pid, last in partners.items():
        u = umap.get(pid)
        if u:
            out.append({"user": u, "last_message": last["text"], "last_at": last["created_at"]})
    return out

@api_router.get("/messages/{other_id}")
async def get_messages(other_id: str, user: dict = Depends(get_current_user)):
    msgs = await db.messages.find({"$or": [
        {"from_user_id": user["id"], "to_user_id": other_id},
        {"from_user_id": other_id, "to_user_id": user["id"]}]}).sort("created_at", 1).to_list(1000)
    connected = await are_connected(user["id"], other_id)
    sent = await db.messages.count_documents({"from_user_id": user["id"], "to_user_id": other_id})
    return {
        "messages": [clean(m) for m in msgs],
        "connected": connected,
        "can_send": connected or sent < 1,
    }

@api_router.post("/messages")
async def post_message(data: MessageInput, user: dict = Depends(get_current_user)):
    connected = await are_connected(user["id"], data.to_user_id)
    if not connected:
        sent = await db.messages.count_documents({"from_user_id": user["id"], "to_user_id": data.to_user_id})
        if sent >= 1:
            raise HTTPException(status_code=403,
                                detail="You can only send one message until you connect. Send a connection request to keep chatting.")
    doc = {"from_user_id": user["id"], "to_user_id": data.to_user_id,
           "text": data.text, "created_at": now_iso()}
    res = await db.messages.insert_one(doc)
    doc["_id"] = res.inserted_id
    return clean(doc)

@api_router.get("/forum")
async def list_forum(community: Optional[str] = None, user: dict = Depends(get_current_user)):
    q = {"community": community} if community else {}
    posts = await db.forum_posts.find(q).sort("created_at", -1).to_list(200)
    umap = await user_map([p["author_id"] for p in posts])
    counts = {}
    if posts:
        pipeline = [{"$match": {"post_id": {"$in": [str(p["_id"]) for p in posts]}}},
                    {"$group": {"_id": "$post_id", "n": {"$sum": 1}}}]
        async for row in db.forum_comments.aggregate(pipeline):
            counts[row["_id"]] = row["n"]
    out = []
    for p in posts:
        p = clean(p)
        p["author"] = umap.get(p["author_id"])
        p["comment_count"] = counts.get(p["id"], 0)
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
    umap = await user_map([c["author_id"] for c in comments])
    out = []
    for c in comments:
        c = clean(c)
        c["author"] = umap.get(c["author_id"])
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
    opps = await db.opportunities.find().sort("created_at", -1).to_list(200)
    students = await db.users.find({"role": "student"}).to_list(50)
    suggested = [clean(s) for s in students if str(s["_id"]) != user["id"]][:4]
    connections_count = await db.connections.count_documents({"status": "accepted", "$or": [
        {"requester_id": user["id"]}, {"recipient_id": user["id"]},
    ]})
    requests_count = await db.connections.count_documents({"recipient_id": user["id"], "status": "pending"})
    return {
        "my_projects": [clean(p) for p in my_projects],
        "opportunities": [clean(o) for o in opps],
        "suggested_teammates": suggested,
        "stats": {
            "projects": len(my_projects),
            "connections": connections_count,
            "connection_requests": requests_count,
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
        rep = dict(s["reputation"])
        rep.setdefault("avg_rating", 0)
        rep.setdefault("review_count", 0)
        rep.pop("endorsements", None)
        doc = {
            "email": s["email"], "password_hash": hash_password("password123"),
            "name": s["name"], "school": s["school"], "grade": s["grade"],
            "bio": s["bio"], "avatar": f"https://api.dicebear.com/7.x/thumbs/svg?seed={s['name'].replace(' ','')}",
            "interests": s["interests"], "skills": s["skills"], "looking_for": s["looking_for"],
            "location": s.get("location", ""),
            "verified": True, "role": "student",
            "reputation": rep, "created_at": now_iso(),
        }
        res = await db.users.insert_one(doc)
        id_map[s["name"]] = str(res.inserted_id)

    for p in PROJECTS:
        owner = id_map[p["owner"]]
        member_ids = [owner] + [id_map[m] for m in p.get("members", []) if m in id_map and id_map[m] != owner]
        await db.projects.insert_one({
            "title": p["title"], "description": p["description"], "category": p["category"],
            "roles_needed": p["roles_needed"], "skills": p["skills"], "timeline": p["timeline"],
            "owner_id": owner, "members": member_ids, "applicants": [],
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
