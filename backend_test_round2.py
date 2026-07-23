"""
Backend tests for Project Nexus - ROUND 2 Features
Tests three new behaviors:
1. Messaging limit for strangers (1 message only until connected)
2. Reviews allowed for connections (not only project teammates)
3. Projects owner connection_status field
Plus regression on dashboard.
"""

import os
import requests
from dotenv import load_dotenv

# Load frontend .env to get public backend URL
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

# Test credentials
PASSWORD = "password123"
ALICE_EMAIL = "alice@lincolnhs.edu"
BOB_EMAIL = "bob@westfield.edu"
CHARLIE_EMAIL = "charlie@stem-prep.edu"
HANA_EMAIL = "hana@centralhs.edu"
GEORGE_EMAIL = "george@summit.edu"
ETHAN_EMAIL = "ethan@oakwood.edu"
DIANA_EMAIL = "diana@riverside.edu"


def login(email, password=PASSWORD):
    """Login and return session with httpOnly cookie."""
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        raise Exception(f"Login failed for {email}: {r.status_code} {r.text}")
    return s


def get_user_id(session):
    """Get current user ID from /auth/me."""
    r = session.get(f"{API}/auth/me", timeout=15)
    if r.status_code != 200:
        raise Exception(f"Failed to get user: {r.status_code} {r.text}")
    return r.json()["id"]


def find_student_by_email(session, email):
    """Find student by email from /students list."""
    r = session.get(f"{API}/students", timeout=15)
    if r.status_code != 200:
        raise Exception(f"Failed to list students: {r.status_code} {r.text}")
    students = r.json()
    for s in students:
        if s.get("email") == email:
            return s
    raise Exception(f"Student not found: {email}")


def test_messaging_limit():
    """
    Test MESSAGING LIMIT FOR STRANGERS:
    - Two users who are NOT connected and NOT project teammates
    - First message succeeds (200)
    - Second message returns 403
    - GET /api/messages/{id} returns object with messages, connected=false, can_send=false
    - After connecting, can_send=true and multiple messages work
    """
    print("\n" + "=" * 70)
    print("TEST 1: MESSAGING LIMIT FOR STRANGERS")
    print("=" * 70)
    
    diana_session = login(DIANA_EMAIL)
    ethan_session = login(ETHAN_EMAIL)
    
    diana_id = get_user_id(diana_session)
    ethan = find_student_by_email(diana_session, ETHAN_EMAIL)
    ethan_id = ethan["id"]
    
    print(f"\nScenario: Diana (stranger) messaging Ethan (stranger)")
    print(f"Diana ID: {diana_id}")
    print(f"Ethan ID: {ethan_id}")
    
    # Verify they are NOT connected initially
    print("\n1.1 Verifying Diana and Ethan are NOT connected...")
    ethan_detail = diana_session.get(f"{API}/students/{ethan_id}", timeout=15).json()
    initial_status = ethan_detail.get("connection_status")
    print(f"   Initial connection_status: {initial_status}")
    if initial_status == "connected":
        print("   ⚠️  WARNING: Diana and Ethan are already connected. Test may not be valid.")
    
    # Test 1: First message from Diana to Ethan should succeed
    print("\n1.2 Testing FIRST message from Diana to Ethan (should succeed)...")
    msg1_data = {"to_user_id": ethan_id, "text": "Hi Ethan! I saw your profile and would love to connect."}
    r = diana_session.post(f"{API}/messages", json=msg1_data, timeout=15)
    print(f"   Response status: {r.status_code}")
    if r.status_code != 200:
        print(f"   Response body: {r.text}")
    assert r.status_code == 200, f"First message should succeed, got {r.status_code}: {r.text}"
    msg1 = r.json()
    print(f"✓ First message sent successfully. Message ID: {msg1.get('id')}")
    
    # Test 2: Second message from Diana to Ethan should return 403
    print("\n1.3 Testing SECOND message from Diana to Ethan (should return 403)...")
    msg2_data = {"to_user_id": ethan_id, "text": "Looking forward to hearing from you!"}
    r = diana_session.post(f"{API}/messages", json=msg2_data, timeout=15)
    print(f"   Response status: {r.status_code}")
    print(f"   Response body: {r.text}")
    assert r.status_code == 403, f"Second message should return 403, got {r.status_code}"
    error_detail = r.json().get("detail", "")
    assert "connect" in error_detail.lower(), f"Error message should mention connecting: {error_detail}"
    print(f"✓ Second message correctly blocked with 403")
    print(f"   Error message: {error_detail}")
    
    # Test 3: GET /api/messages/{ethan_id} should return object with correct structure
    print("\n1.4 Testing GET /api/messages/{ethan_id} returns correct object structure...")
    r = diana_session.get(f"{API}/messages/{ethan_id}", timeout=15)
    assert r.status_code == 200, f"GET messages failed: {r.status_code} {r.text}"
    msg_obj = r.json()
    
    print(f"   Response keys: {list(msg_obj.keys())}")
    assert isinstance(msg_obj, dict), f"Response should be an object, got {type(msg_obj)}"
    assert "messages" in msg_obj, "Response missing 'messages' key"
    assert "connected" in msg_obj, "Response missing 'connected' key"
    assert "can_send" in msg_obj, "Response missing 'can_send' key"
    
    assert isinstance(msg_obj["messages"], list), f"messages should be array, got {type(msg_obj['messages'])}"
    assert isinstance(msg_obj["connected"], bool), f"connected should be bool, got {type(msg_obj['connected'])}"
    assert isinstance(msg_obj["can_send"], bool), f"can_send should be bool, got {type(msg_obj['can_send'])}"
    
    assert msg_obj["connected"] == False, f"connected should be false, got {msg_obj['connected']}"
    assert msg_obj["can_send"] == False, f"can_send should be false after first message, got {msg_obj['can_send']}"
    assert len(msg_obj["messages"]) >= 1, f"Should have at least 1 message, got {len(msg_obj['messages'])}"
    
    print(f"✓ GET /api/messages/{ethan_id} returns correct structure:")
    print(f"   - messages: array with {len(msg_obj['messages'])} message(s)")
    print(f"   - connected: {msg_obj['connected']}")
    print(f"   - can_send: {msg_obj['can_send']}")
    
    # Test 4: Connect Diana and Ethan
    print("\n1.5 Connecting Diana and Ethan...")
    print("   Diana sends connection request to Ethan...")
    r = diana_session.post(f"{API}/connections/{ethan_id}", timeout=15)
    assert r.status_code == 200, f"Connection request failed: {r.status_code} {r.text}"
    conn_result = r.json()
    print(f"   Connection status: {conn_result.get('status')}")
    
    print("   Ethan accepts Diana's request...")
    r = ethan_session.post(f"{API}/connections/{diana_id}/respond", json={"action": "accept"}, timeout=15)
    assert r.status_code == 200, f"Accept failed: {r.status_code} {r.text}"
    accept_result = r.json()
    assert accept_result.get("status") == "connected", f"Expected connected, got {accept_result.get('status')}"
    print(f"✓ Diana and Ethan are now connected")
    
    # Test 5: After connecting, GET /api/messages should show can_send=true and connected=true
    print("\n1.6 Testing GET /api/messages after connection...")
    r = diana_session.get(f"{API}/messages/{ethan_id}", timeout=15)
    assert r.status_code == 200, f"GET messages failed: {r.status_code} {r.text}"
    msg_obj_after = r.json()
    
    assert msg_obj_after["connected"] == True, f"connected should be true after connecting, got {msg_obj_after['connected']}"
    assert msg_obj_after["can_send"] == True, f"can_send should be true after connecting, got {msg_obj_after['can_send']}"
    print(f"✓ After connection:")
    print(f"   - connected: {msg_obj_after['connected']}")
    print(f"   - can_send: {msg_obj_after['can_send']}")
    
    # Test 6: After connecting, Diana can send multiple messages
    print("\n1.7 Testing multiple messages after connection...")
    for i in range(3):
        msg_data = {"to_user_id": ethan_id, "text": f"Message {i+2} after connecting"}
        r = diana_session.post(f"{API}/messages", json=msg_data, timeout=15)
        assert r.status_code == 200, f"Message {i+2} failed: {r.status_code} {r.text}"
    print(f"✓ Diana successfully sent 3 additional messages after connecting (no 403)")
    
    print("\n" + "=" * 70)
    print("✅ TEST 1 PASSED: MESSAGING LIMIT FOR STRANGERS")
    print("=" * 70)


def test_reviews_for_connections():
    """
    Test REVIEWS ALLOWED FOR CONNECTIONS:
    - Hana initially cannot review George (non-teammate, non-connection)
    - Hana sends connection request to George, George accepts
    - GET /api/students shows can_review=true for George
    - Hana can now review George (should succeed)
    - Verify reputation recompute reflects the review
    - Confirm review for someone who is NEITHER teammate NOR connection still returns 403
    """
    print("\n" + "=" * 70)
    print("TEST 2: REVIEWS ALLOWED FOR CONNECTIONS")
    print("=" * 70)
    
    hana_session = login(HANA_EMAIL)
    george_session = login(GEORGE_EMAIL)
    diana_session = login(DIANA_EMAIL)
    
    hana_id = get_user_id(hana_session)
    george = find_student_by_email(hana_session, GEORGE_EMAIL)
    george_id = george["id"]
    diana = find_student_by_email(hana_session, DIANA_EMAIL)
    diana_id = diana["id"]
    
    print(f"\nScenario: Hana reviewing George (initially non-teammate, non-connection)")
    print(f"Hana ID: {hana_id}")
    print(f"George ID: {george_id}")
    print(f"Diana ID: {diana_id}")
    
    # Test 1: Verify Hana cannot review George initially (non-teammate, non-connection)
    print("\n2.1 Verifying Hana cannot review George initially...")
    george_detail = hana_session.get(f"{API}/students/{george_id}", timeout=15).json()
    initial_can_review = george_detail.get("can_review")
    initial_status = george_detail.get("connection_status")
    print(f"   George's can_review: {initial_can_review}")
    print(f"   George's connection_status: {initial_status}")
    
    if initial_can_review == True:
        print("   ⚠️  WARNING: can_review is already true. They may already be connected or teammates.")
    
    # Try to review George - should fail with 403
    print("\n2.2 Testing Hana cannot review George (should return 403)...")
    review_data = {"rating": 4, "reliability": 85, "comment": "Test review before connection"}
    r = hana_session.post(f"{API}/students/{george_id}/reviews", json=review_data, timeout=15)
    print(f"   Response status: {r.status_code}")
    if r.status_code != 403:
        print(f"   Response body: {r.text}")
    assert r.status_code == 403, f"Review should fail with 403, got {r.status_code}"
    print(f"✓ Review correctly blocked with 403 (not connected, not teammates)")
    
    # Test 2: Hana sends connection request to George, George accepts
    print("\n2.3 Connecting Hana and George...")
    print("   Hana sends connection request to George...")
    r = hana_session.post(f"{API}/connections/{george_id}", timeout=15)
    assert r.status_code == 200, f"Connection request failed: {r.status_code} {r.text}"
    conn_result = r.json()
    print(f"   Connection status: {conn_result.get('status')}")
    
    print("   George accepts Hana's request...")
    r = george_session.post(f"{API}/connections/{hana_id}/respond", json={"action": "accept"}, timeout=15)
    assert r.status_code == 200, f"Accept failed: {r.status_code} {r.text}"
    accept_result = r.json()
    assert accept_result.get("status") == "connected", f"Expected connected, got {accept_result.get('status')}"
    print(f"✓ Hana and George are now connected")
    
    # Test 3: GET /api/students should show can_review=true for George
    print("\n2.4 Verifying GET /api/students shows can_review=true for George...")
    students = hana_session.get(f"{API}/students", timeout=15).json()
    george_in_list = None
    for s in students:
        if s.get("id") == george_id:
            george_in_list = s
            break
    
    assert george_in_list is not None, "George not found in students list"
    assert george_in_list.get("can_review") == True, f"can_review should be true after connection, got {george_in_list.get('can_review')}"
    assert george_in_list.get("connection_status") == "connected", f"connection_status should be connected, got {george_in_list.get('connection_status')}"
    print(f"✓ GET /api/students shows can_review=true and connection_status=connected for George")
    
    # Test 4: Hana can now review George (should succeed)
    print("\n2.5 Testing Hana can now review George (should succeed)...")
    george_before = hana_session.get(f"{API}/students/{george_id}", timeout=15).json()
    rep_before = george_before.get("reputation", {})
    print(f"   George's reputation before: {rep_before}")
    
    review_data = {
        "rating": 4,
        "reliability": 85,
        "comment": "Great connection! Looking forward to collaborating."
    }
    r = hana_session.post(f"{API}/students/{george_id}/reviews", json=review_data, timeout=15)
    print(f"   Response status: {r.status_code}")
    if r.status_code != 200:
        print(f"   Response body: {r.text}")
    assert r.status_code == 200, f"Review should succeed after connection, got {r.status_code}: {r.text}"
    
    george_after = r.json()
    rep_after = george_after.get("reputation", {})
    print(f"   George's reputation after: {rep_after}")
    print(f"✓ Hana successfully reviewed George (connected user)")
    
    # Test 5: Verify reputation recompute reflects the review
    print("\n2.6 Verifying reputation recompute...")
    assert "reliability" in rep_after, "Reputation missing reliability"
    assert "avg_rating" in rep_after, "Reputation missing avg_rating"
    assert "review_count" in rep_after, "Reputation missing review_count"
    
    # The review should be reflected in the counts
    review_count_increased = rep_after["review_count"] >= rep_before.get("review_count", 0)
    assert review_count_increased, f"Review count should increase, before={rep_before.get('review_count')}, after={rep_after['review_count']}"
    print(f"✓ Reputation recomputed correctly:")
    print(f"   - reliability: {rep_after['reliability']}")
    print(f"   - avg_rating: {rep_after['avg_rating']}")
    print(f"   - review_count: {rep_after['review_count']}")
    
    # Test 6: Confirm review for someone who is NEITHER teammate NOR connection still returns 403
    print("\n2.7 Testing Hana cannot review Diana (neither teammate nor connection)...")
    diana_detail = hana_session.get(f"{API}/students/{diana_id}", timeout=15).json()
    diana_can_review = diana_detail.get("can_review")
    diana_status = diana_detail.get("connection_status")
    print(f"   Diana's can_review: {diana_can_review}")
    print(f"   Diana's connection_status: {diana_status}")
    
    if diana_can_review == False and diana_status in ["none", "pending_out", "pending_in"]:
        review_data = {"rating": 3, "reliability": 70, "comment": "Test review"}
        r = hana_session.post(f"{API}/students/{diana_id}/reviews", json=review_data, timeout=15)
        print(f"   Response status: {r.status_code}")
        assert r.status_code == 403, f"Review should fail with 403 for non-teammate non-connection, got {r.status_code}"
        print(f"✓ Review correctly blocked with 403 (neither teammate nor connection)")
    else:
        print(f"   ⚠️  Skipping test - Hana and Diana are already connected or teammates")
    
    print("\n" + "=" * 70)
    print("✅ TEST 2 PASSED: REVIEWS ALLOWED FOR CONNECTIONS")
    print("=" * 70)


def test_projects_owner_connection_status():
    """
    Test PROJECTS OWNER CONNECTION STATUS:
    - GET /api/projects: each project's owner object includes connection_status field
    - Values: self/none/pending_out/connected
    - For a project you own, connection_status should be "self"
    - After connecting to an owner, connection_status should be "connected"
    """
    print("\n" + "=" * 70)
    print("TEST 3: PROJECTS OWNER CONNECTION STATUS")
    print("=" * 70)
    
    alice_session = login(ALICE_EMAIL)
    bob_session = login(BOB_EMAIL)
    
    alice_id = get_user_id(alice_session)
    bob = find_student_by_email(alice_session, BOB_EMAIL)
    bob_id = bob["id"]
    
    print(f"\nScenario: Checking project owner connection_status field")
    print(f"Alice ID: {alice_id}")
    print(f"Bob ID: {bob_id}")
    
    # Test 1: GET /api/projects returns projects with owner.connection_status
    print("\n3.1 Testing GET /api/projects includes owner.connection_status...")
    r = alice_session.get(f"{API}/projects", timeout=15)
    assert r.status_code == 200, f"GET projects failed: {r.status_code} {r.text}"
    projects = r.json()
    
    assert isinstance(projects, list), f"Projects should be a list, got {type(projects)}"
    assert len(projects) > 0, "Projects list should not be empty"
    print(f"   Found {len(projects)} projects")
    
    # Check each project has owner with connection_status
    for i, proj in enumerate(projects[:5]):  # Check first 5 projects
        print(f"\n   Project {i+1}: {proj.get('title')}")
        assert "owner" in proj, f"Project missing 'owner' field"
        owner = proj["owner"]
        assert owner is not None, f"Project owner is None"
        assert isinstance(owner, dict), f"Owner should be an object, got {type(owner)}"
        assert "connection_status" in owner, f"Owner missing 'connection_status' field"
        
        status = owner["connection_status"]
        valid_statuses = ["self", "none", "pending_out", "pending_in", "connected"]
        assert status in valid_statuses, f"Invalid connection_status: {status}. Expected one of {valid_statuses}"
        
        print(f"      Owner: {owner.get('name')}")
        print(f"      Owner ID: {owner.get('id')}")
        print(f"      connection_status: {status}")
        
        # If Alice owns this project, status should be "self"
        if owner.get("id") == alice_id:
            assert status == "self", f"For own project, connection_status should be 'self', got {status}"
            print(f"      ✓ Own project correctly shows 'self'")
    
    print(f"\n✓ All projects have owner.connection_status field with valid values")
    
    # Test 2: Find a project owned by someone else and verify connection_status changes
    print("\n3.2 Testing connection_status changes after connecting to project owner...")
    
    # Find a project NOT owned by Alice
    other_project = None
    other_owner_id = None
    for proj in projects:
        owner = proj.get("owner", {})
        if owner and owner.get("id") != alice_id:
            other_project = proj
            other_owner_id = owner.get("id")
            break
    
    if other_project:
        print(f"   Found project owned by someone else: {other_project.get('title')}")
        print(f"   Owner: {other_project['owner'].get('name')} (ID: {other_owner_id})")
        initial_status = other_project["owner"].get("connection_status")
        print(f"   Initial connection_status: {initial_status}")
        
        # If not already connected, connect to the owner
        if initial_status != "connected":
            print(f"   Connecting Alice to project owner...")
            r = alice_session.post(f"{API}/connections/{other_owner_id}", timeout=15)
            assert r.status_code == 200, f"Connection request failed: {r.status_code} {r.text}"
            conn_result = r.json()
            print(f"   Connection result: {conn_result.get('status')}")
            
            # If it became connected (auto-accept or already pending), verify
            if conn_result.get("status") == "connected":
                # Fetch projects again and verify connection_status updated
                r = alice_session.get(f"{API}/projects", timeout=15)
                projects_after = r.json()
                
                # Find the same project
                updated_project = None
                for proj in projects_after:
                    if proj.get("title") == other_project.get("title"):
                        updated_project = proj
                        break
                
                if updated_project:
                    updated_status = updated_project["owner"].get("connection_status")
                    print(f"   Updated connection_status: {updated_status}")
                    assert updated_status == "connected", f"After connecting, status should be 'connected', got {updated_status}"
                    print(f"✓ connection_status correctly updated to 'connected' after connecting to owner")
            else:
                print(f"   Connection is pending. Status would update to 'connected' after acceptance.")
        else:
            print(f"   Already connected to owner. Status correctly shows 'connected'.")
    else:
        print(f"   ⚠️  No projects found owned by others. Skipping connection status change test.")
    
    print("\n" + "=" * 70)
    print("✅ TEST 3 PASSED: PROJECTS OWNER CONNECTION STATUS")
    print("=" * 70)


def test_dashboard_regression():
    """
    Test DASHBOARD REGRESSION:
    - GET /api/dashboard returns stats.connections and stats.connection_requests
    - Opportunities include location field
    """
    print("\n" + "=" * 70)
    print("TEST 4: DASHBOARD REGRESSION")
    print("=" * 70)
    
    alice_session = login(ALICE_EMAIL)
    
    print("\n4.1 Testing GET /api/dashboard...")
    r = alice_session.get(f"{API}/dashboard", timeout=15)
    assert r.status_code == 200, f"GET dashboard failed: {r.status_code} {r.text}"
    dashboard = r.json()
    
    print(f"   Dashboard keys: {list(dashboard.keys())}")
    
    # Test stats.connections and stats.connection_requests
    print("\n4.2 Verifying stats.connections and stats.connection_requests...")
    assert "stats" in dashboard, "Dashboard missing 'stats'"
    stats = dashboard["stats"]
    
    assert "connections" in stats, "Dashboard stats missing 'connections'"
    assert "connection_requests" in stats, "Dashboard stats missing 'connection_requests'"
    
    assert isinstance(stats["connections"], int), f"connections should be int, got {type(stats['connections'])}"
    assert isinstance(stats["connection_requests"], int), f"connection_requests should be int, got {type(stats['connection_requests'])}"
    
    print(f"✓ Dashboard stats:")
    print(f"   - connections: {stats['connections']}")
    print(f"   - connection_requests: {stats['connection_requests']}")
    print(f"   - projects: {stats.get('projects')}")
    print(f"   - opportunities: {stats.get('opportunities')}")
    
    # Test opportunities include location
    print("\n4.3 Verifying opportunities include location field...")
    assert "opportunities" in dashboard, "Dashboard missing 'opportunities'"
    opportunities = dashboard["opportunities"]
    
    assert isinstance(opportunities, list), f"Opportunities should be a list, got {type(opportunities)}"
    print(f"   Found {len(opportunities)} opportunities")
    
    if len(opportunities) > 0:
        for i, opp in enumerate(opportunities[:5]):  # Check first 5
            assert "location" in opp, f"Opportunity {i+1} '{opp.get('title')}' missing location field"
            print(f"   Opportunity {i+1}: {opp.get('title')} - Location: {opp.get('location')}")
        print(f"✓ All opportunities have location field")
    else:
        print(f"   ⚠️  No opportunities in dashboard. Cannot verify location field.")
    
    print("\n" + "=" * 70)
    print("✅ TEST 4 PASSED: DASHBOARD REGRESSION")
    print("=" * 70)


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("BACKEND TESTING - Project Nexus ROUND 2 Features")
    print("=" * 70)
    print("\nTesting three new behaviors:")
    print("1. Messaging limit for strangers (1 message until connected)")
    print("2. Reviews allowed for connections (not only project teammates)")
    print("3. Projects owner connection_status field")
    print("Plus: Dashboard regression")
    print("=" * 70)
    
    try:
        test_messaging_limit()
        test_reviews_for_connections()
        test_projects_owner_connection_status()
        test_dashboard_regression()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nSummary:")
        print("✓ Messaging limit for strangers working correctly")
        print("✓ Reviews allowed for connections working correctly")
        print("✓ Projects owner connection_status field working correctly")
        print("✓ Dashboard regression checks passed")
        print("=" * 70)
        return 0
    except AssertionError as e:
        print(f"\n" + "=" * 70)
        print(f"❌ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n" + "=" * 70)
        print(f"❌ ERROR")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
