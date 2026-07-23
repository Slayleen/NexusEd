"""
Comprehensive backend tests for Project Nexus - Reviews & Connections features.
Tests the newly added backend features as per review request.
"""

import os
import requests
from dotenv import load_dotenv

# Load frontend .env to get public backend URL
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

# Test credentials from test_credentials.md
ALICE_EMAIL = "alice@lincolnhs.edu"
DIANA_EMAIL = "diana@riverside.edu"
BOB_EMAIL = "bob@westfield.edu"
CHARLIE_EMAIL = "charlie@stem-prep.edu"
GEORGE_EMAIL = "george@summit.edu"
PASSWORD = "password123"


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


def test_reviews():
    """Test Reviews API functionality."""
    print("\n=== Testing REVIEWS ===")
    
    alice_session = login(ALICE_EMAIL)
    diana_session = login(DIANA_EMAIL)
    
    # Get student IDs
    bob = find_student_by_email(alice_session, BOB_EMAIL)
    bob_id = bob["id"]
    diana = find_student_by_email(alice_session, DIANA_EMAIL)
    diana_id = diana["id"]
    alice_id = get_user_id(alice_session)
    
    # Test 1: GET /api/students returns can_review and connection_status and location
    print("\n1. Testing GET /api/students returns can_review, connection_status, location...")
    students = alice_session.get(f"{API}/students", timeout=15).json()
    assert isinstance(students, list) and len(students) > 0, "Students list should not be empty"
    
    for s in students:
        assert "can_review" in s, f"Student {s.get('name')} missing can_review field"
        assert isinstance(s["can_review"], bool), f"can_review should be bool, got {type(s['can_review'])}"
        assert "connection_status" in s, f"Student {s.get('name')} missing connection_status field"
        assert s["connection_status"] in ["none", "pending_out", "pending_in", "connected"], \
            f"Invalid connection_status: {s['connection_status']}"
        assert "location" in s, f"Student {s.get('name')} missing location field"
    print("✓ All students have can_review, connection_status, and location fields")
    
    # Test 2: Alice can review Bob (teammate) - should succeed
    print(f"\n2. Testing Alice can review Bob (teammate)...")
    bob_before = alice_session.get(f"{API}/students/{bob_id}", timeout=15).json()
    print(f"   Bob's reputation before: {bob_before.get('reputation')}")
    
    review_data = {
        "rating": 5,
        "reliability": 90,
        "comment": "Great teammate! Very reliable and skilled."
    }
    r = alice_session.post(f"{API}/students/{bob_id}/reviews", json=review_data, timeout=15)
    assert r.status_code == 200, f"Review creation failed: {r.status_code} {r.text}"
    
    bob_after = r.json()
    print(f"   Bob's reputation after: {bob_after.get('reputation')}")
    
    # Verify reputation updated
    rep = bob_after.get("reputation", {})
    assert "reliability" in rep, "Reputation missing reliability"
    assert "avg_rating" in rep, "Reputation missing avg_rating"
    assert "review_count" in rep, "Reputation missing review_count"
    assert rep["review_count"] >= 1, f"Review count should be >= 1, got {rep['review_count']}"
    print(f"✓ Alice successfully reviewed Bob. Reputation updated: reliability={rep['reliability']}, avg_rating={rep['avg_rating']}, review_count={rep['review_count']}")
    
    # Test 3: Alice cannot review Diana (non-teammate) - should return 403
    print(f"\n3. Testing Alice cannot review Diana (non-teammate)...")
    r = alice_session.post(f"{API}/students/{diana_id}/reviews", json=review_data, timeout=15)
    assert r.status_code == 403, f"Expected 403 for non-teammate review, got {r.status_code}"
    print("✓ Correctly blocked review of non-teammate (403)")
    
    # Test 4: Posting second review from Alice to Bob should UPSERT (not duplicate)
    print(f"\n4. Testing review upsert (second review from Alice to Bob)...")
    review_data2 = {
        "rating": 4,
        "reliability": 85,
        "comment": "Updated review - still great!"
    }
    r = alice_session.post(f"{API}/students/{bob_id}/reviews", json=review_data2, timeout=15)
    assert r.status_code == 200, f"Review update failed: {r.status_code} {r.text}"
    
    # Get reviews list to verify only one review from Alice
    reviews = alice_session.get(f"{API}/students/{bob_id}/reviews", timeout=15).json()
    alice_reviews = [rev for rev in reviews if rev.get("reviewer_id") == alice_id]
    assert len(alice_reviews) == 1, f"Expected 1 review from Alice, got {len(alice_reviews)}"
    assert alice_reviews[0]["rating"] == 4, f"Review should be updated to rating 4, got {alice_reviews[0]['rating']}"
    print(f"✓ Review upserted correctly. Only 1 review from Alice with updated values.")
    
    # Test 5: GET /api/students/{bob_id}/reviews returns list with reviewer info
    print(f"\n5. Testing GET /api/students/{bob_id}/reviews...")
    reviews = alice_session.get(f"{API}/students/{bob_id}/reviews", timeout=15).json()
    assert isinstance(reviews, list), "Reviews should be a list"
    if len(reviews) > 0:
        for rev in reviews:
            assert "reviewer" in rev, "Review missing reviewer info"
            assert "rating" in rev, "Review missing rating"
            assert "reliability" in rev, "Review missing reliability"
            assert "comment" in rev, "Review missing comment"
        print(f"✓ Reviews list returned correctly with {len(reviews)} review(s)")
    else:
        print("✓ Reviews list returned (empty)")
    
    # Test 6: Reviewing yourself returns 400
    print(f"\n6. Testing self-review prevention...")
    r = alice_session.post(f"{API}/students/{alice_id}/reviews", json=review_data, timeout=15)
    assert r.status_code == 400, f"Expected 400 for self-review, got {r.status_code}"
    print("✓ Self-review correctly blocked (400)")
    
    print("\n✅ All REVIEWS tests passed!")


def test_connections():
    """Test Connections API functionality."""
    print("\n=== Testing CONNECTIONS ===")
    
    alice_session = login(ALICE_EMAIL)
    diana_session = login(DIANA_EMAIL)
    george_session = login(GEORGE_EMAIL)
    
    alice_id = get_user_id(alice_session)
    diana = find_student_by_email(alice_session, DIANA_EMAIL)
    diana_id = diana["id"]
    george = find_student_by_email(diana_session, GEORGE_EMAIL)
    george_id = george["id"]
    
    # Test 1: Alice sends connection request to Diana
    print(f"\n1. Testing Alice sends connection request to Diana...")
    r = alice_session.post(f"{API}/connections/{diana_id}", timeout=15)
    assert r.status_code == 200, f"Connection request failed: {r.status_code} {r.text}"
    result = r.json()
    assert result.get("status") == "pending_out", f"Expected pending_out, got {result.get('status')}"
    print(f"✓ Connection request sent. Status: {result.get('status')}")
    
    # Test 2: Diana sees Alice in connection requests
    print(f"\n2. Testing Diana sees Alice in connection requests...")
    r = diana_session.get(f"{API}/connections/requests", timeout=15)
    assert r.status_code == 200, f"Failed to get requests: {r.status_code} {r.text}"
    requests_list = r.json()
    assert isinstance(requests_list, list), "Requests should be a list"
    alice_request = None
    for req in requests_list:
        if req.get("email") == ALICE_EMAIL:
            alice_request = req
            break
    assert alice_request is not None, f"Alice's request not found in Diana's requests. Got: {requests_list}"
    print(f"✓ Diana sees Alice's connection request")
    
    # Test 3: Diana accepts Alice's request
    print(f"\n3. Testing Diana accepts Alice's request...")
    r = diana_session.post(f"{API}/connections/{alice_id}/respond", json={"action": "accept"}, timeout=15)
    assert r.status_code == 200, f"Accept failed: {r.status_code} {r.text}"
    result = r.json()
    assert result.get("status") == "connected", f"Expected connected, got {result.get('status')}"
    print(f"✓ Connection accepted. Status: {result.get('status')}")
    
    # Test 4: Both Alice and Diana see each other in connections list
    print(f"\n4. Testing both users see each other in connections list...")
    alice_connections = alice_session.get(f"{API}/connections", timeout=15).json()
    diana_connections = diana_session.get(f"{API}/connections", timeout=15).json()
    
    diana_in_alice = any(c.get("id") == diana_id for c in alice_connections)
    alice_in_diana = any(c.get("id") == alice_id for c in diana_connections)
    
    assert diana_in_alice, f"Diana not in Alice's connections. Got: {[c.get('name') for c in alice_connections]}"
    assert alice_in_diana, f"Alice not in Diana's connections. Got: {[c.get('name') for c in diana_connections]}"
    print(f"✓ Both users see each other in connections list")
    
    # Test 5: Dashboard stats reflect connections
    print(f"\n5. Testing dashboard stats.connections and stats.connection_requests...")
    alice_dash = alice_session.get(f"{API}/dashboard", timeout=15).json()
    diana_dash = diana_session.get(f"{API}/dashboard", timeout=15).json()
    
    assert "stats" in alice_dash, "Dashboard missing stats"
    assert "connections" in alice_dash["stats"], "Dashboard stats missing connections"
    assert "connection_requests" in alice_dash["stats"], "Dashboard stats missing connection_requests"
    
    alice_conn_count = alice_dash["stats"]["connections"]
    diana_conn_count = diana_dash["stats"]["connections"]
    
    assert alice_conn_count >= 1, f"Alice should have at least 1 connection, got {alice_conn_count}"
    assert diana_conn_count >= 1, f"Diana should have at least 1 connection, got {diana_conn_count}"
    print(f"✓ Dashboard stats: Alice connections={alice_conn_count}, Diana connections={diana_conn_count}")
    
    # Test 6: Decline flow - Diana sends request to George, George declines
    print(f"\n6. Testing decline flow...")
    r = diana_session.post(f"{API}/connections/{george_id}", timeout=15)
    assert r.status_code == 200, f"Connection request failed: {r.status_code} {r.text}"
    
    # George sees the request
    george_requests = george_session.get(f"{API}/connections/requests", timeout=15).json()
    diana_request = any(req.get("id") == diana_id for req in george_requests)
    assert diana_request, "Diana's request not found in George's requests"
    
    # George declines
    r = george_session.post(f"{API}/connections/{diana_id}/respond", json={"action": "decline"}, timeout=15)
    assert r.status_code == 200, f"Decline failed: {r.status_code} {r.text}"
    result = r.json()
    assert result.get("status") == "none", f"Expected none after decline, got {result.get('status')}"
    
    # Request should disappear from George's requests
    george_requests_after = george_session.get(f"{API}/connections/requests", timeout=15).json()
    diana_request_after = any(req.get("id") == diana_id for req in george_requests_after)
    assert not diana_request_after, "Diana's request should be removed after decline"
    print(f"✓ Decline flow works correctly. Status: {result.get('status')}")
    
    # Test 7: Auto-accept - if B has pending from A, and B posts to A, it becomes connected
    print(f"\n7. Testing auto-accept flow...")
    # Create a new connection scenario - we'll use existing users
    # First, clean up any existing connection between Diana and George
    # Diana sends request to George again
    r = diana_session.post(f"{API}/connections/{george_id}", timeout=15)
    assert r.status_code == 200, f"Connection request failed: {r.status_code} {r.text}"
    result = r.json()
    # If it's already pending_out, that's fine
    assert result.get("status") in ["pending_out", "connected"], f"Expected pending_out or connected, got {result.get('status')}"
    
    if result.get("status") == "pending_out":
        # Now George sends request to Diana (reverse) - should auto-accept
        r = george_session.post(f"{API}/connections/{diana_id}", timeout=15)
        assert r.status_code == 200, f"Auto-accept failed: {r.status_code} {r.text}"
        result = r.json()
        assert result.get("status") == "connected", f"Expected auto-accept to connected, got {result.get('status')}"
        print(f"✓ Auto-accept works correctly. Status: {result.get('status')}")
    else:
        print(f"✓ Auto-accept test skipped (already connected)")
    
    # Test 8: Prevent self-connect
    print(f"\n8. Testing self-connect prevention...")
    r = alice_session.post(f"{API}/connections/{alice_id}", timeout=15)
    assert r.status_code == 400, f"Expected 400 for self-connect, got {r.status_code}"
    print("✓ Self-connect correctly blocked (400)")
    
    # Test 9: Duplicate handling - sending request again should not create duplicate
    print(f"\n9. Testing duplicate connection handling...")
    # Alice and Diana are already connected, try to send again
    r = alice_session.post(f"{API}/connections/{diana_id}", timeout=15)
    assert r.status_code == 200, f"Duplicate request failed: {r.status_code} {r.text}"
    result = r.json()
    assert result.get("status") == "connected", f"Expected connected for duplicate, got {result.get('status')}"
    print(f"✓ Duplicate connection handled correctly. Status: {result.get('status')}")
    
    print("\n✅ All CONNECTIONS tests passed!")


def test_regression():
    """Test regression items - endorse removed, location fields, etc."""
    print("\n=== Testing REGRESSION / REMOVAL ===")
    
    alice_session = login(ALICE_EMAIL)
    bob = find_student_by_email(alice_session, BOB_EMAIL)
    bob_id = bob["id"]
    
    # Test 1: POST /api/students/{id}/endorse should NOT exist (404 or 405)
    print(f"\n1. Testing endorse endpoint removed...")
    r = alice_session.post(f"{API}/students/{bob_id}/endorse", timeout=15)
    assert r.status_code in [404, 405], f"Expected 404/405 for removed endorse endpoint, got {r.status_code}"
    print(f"✓ Endorse endpoint correctly removed (status {r.status_code})")
    
    # Test 2: Reputation objects should NOT contain 'endorsements'
    print(f"\n2. Testing reputation does not contain endorsements...")
    students = alice_session.get(f"{API}/students", timeout=15).json()
    for s in students:
        rep = s.get("reputation", {})
        assert "endorsements" not in rep, f"Student {s.get('name')} reputation still has endorsements field"
    print(f"✓ No student reputation contains 'endorsements' field")
    
    # Test 3: GET /api/opportunities includes location field
    print(f"\n3. Testing opportunities include location field...")
    opps = alice_session.get(f"{API}/opportunities", timeout=15).json()
    assert isinstance(opps, list) and len(opps) > 0, "Opportunities list should not be empty"
    for opp in opps:
        assert "location" in opp, f"Opportunity {opp.get('title')} missing location field"
    print(f"✓ All {len(opps)} opportunities have location field")
    
    # Test 4: GET /api/dashboard opportunities include location
    print(f"\n4. Testing dashboard opportunities include location...")
    dash = alice_session.get(f"{API}/dashboard", timeout=15).json()
    assert "opportunities" in dash, "Dashboard missing opportunities"
    dash_opps = dash["opportunities"]
    for opp in dash_opps:
        assert "location" in opp, f"Dashboard opportunity {opp.get('title')} missing location field"
    print(f"✓ All {len(dash_opps)} dashboard opportunities have location field")
    
    # Test 5: PUT /api/profile with location persists
    print(f"\n5. Testing profile location field...")
    r = alice_session.put(f"{API}/profile", json={"location": "Boston, MA"}, timeout=15)
    assert r.status_code == 200, f"Profile update failed: {r.status_code} {r.text}"
    
    # Verify via /auth/me
    me = alice_session.get(f"{API}/auth/me", timeout=15).json()
    assert me.get("location") == "Boston, MA", f"Location not persisted. Got: {me.get('location')}"
    print(f"✓ Profile location persisted correctly: {me.get('location')}")
    
    print("\n✅ All REGRESSION tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("BACKEND TESTING - Project Nexus Reviews & Connections")
    print("=" * 60)
    
    try:
        test_reviews()
        test_connections()
        test_regression()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
