#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Add a collaborator review system (star rating 1-5 + reliability score + comment), only between students
  who share a project. Remove the "endorse" feature. Make the reliability indicator driven by reviews
  (average of review reliability, 100% until first review). Add a real connect/accept connection system;
  the dashboard "Students" box becomes "Connections". Opportunities on the dashboard are scoped by the
  student's area/location with a broaden/constrain selector. The "Find teammates" button goes to Discover.

backend:
  - task: "Reviews API (create/list, shared-project gating, reputation recompute)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "POST/GET /api/students/{sid}/reviews. Only allowed if reviewer & reviewee share a project (members). Upsert per reviewer->reviewee. recompute_reputation sets reliability=avg(reliability), avg_rating=avg(rating), review_count. Verified via curl: Alice can review Bob (member) -> rep updated; reviewing Diana returns 403."
        - working: true
          agent: "testing"
          comment: "Comprehensive testing completed. ✓ GET /api/students returns can_review, connection_status, location fields. ✓ Alice successfully reviewed Bob (teammate) - reputation updated correctly (reliability=90, avg_rating=5.0, review_count=1). ✓ Alice blocked from reviewing Diana (non-teammate) with 403. ✓ Review upsert works - second review from Alice to Bob updates existing review (no duplicates). ✓ GET /api/students/{id}/reviews returns list with reviewer info. ✓ Self-review blocked with 400. All review functionality working as expected."
  - task: "Connections API (send/respond/list/requests)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "POST /api/connections/{sid} (auto-accepts if reverse pending), POST /api/connections/{sid}/respond {accept|decline}, GET /api/connections, GET /api/connections/requests. students list/detail include connection_status + can_review. Verified send returns pending_out via curl."
        - working: true
          agent: "testing"
          comment: "Full connection lifecycle tested successfully. ✓ Alice sends request to Diana - returns pending_out. ✓ Diana sees Alice in GET /api/connections/requests. ✓ Diana accepts via POST /api/connections/{alice_id}/respond {action:accept} - returns connected. ✓ Both users see each other in GET /api/connections. ✓ Dashboard stats.connections and stats.connection_requests reflect correct counts (Alice=1, Diana=1). ✓ Decline flow works - Diana->George request declined, status=none, request removed from list. ✓ Auto-accept works - when B has pending from A and B posts to A, becomes connected. ✓ Self-connect blocked with 400. ✓ Duplicate handling works - sending request to already-connected user returns connected. All connection functionality working perfectly."
  - task: "Remove endorse endpoint; dashboard stats connections + connection_requests; opportunities include location"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Removed /students/{sid}/endorse. reputation no longer has endorsements (now avg_rating/review_count). Dashboard returns stats.connections, stats.connection_requests, and all opportunities with location. Profile PUT accepts location. Re-seeded DB with multi-member projects + opportunity locations. NOTE: recreated missing backend/.env and frontend/.env (env files were absent, app was down)."
        - working: true
          agent: "testing"
          comment: "Regression testing completed successfully. ✓ POST /api/students/{id}/endorse returns 404 (correctly removed). ✓ All student reputation objects do NOT contain 'endorsements' field. ✓ GET /api/opportunities returns 10 opportunities, all with location field. ✓ GET /api/dashboard opportunities (10 items) all include location field. ✓ PUT /api/profile with {location:'Boston, MA'} persists and is returned by GET /api/auth/me. All regression requirements met."
  - task: "Messaging limit for strangers (1 message until connected)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "POST /api/messages enforces 1-message limit for non-connected users. GET /api/messages/{id} returns object with {messages, connected, can_send}. Verified via curl: stranger sends 1st msg (200), 2nd msg returns 403."
        - working: true
          agent: "testing"
          comment: "ROUND 2 testing completed. ✓ Diana (stranger) sends first message to Ethan - succeeds (200). ✓ Second message from Diana to Ethan correctly blocked with 403 and appropriate error message. ✓ GET /api/messages/{ethan_id} returns correct object structure with messages (array), connected (false), can_send (false). ✓ After Diana and Ethan connect, GET /api/messages shows connected=true and can_send=true. ✓ Diana successfully sends 3 additional messages after connecting (no 403). All messaging limit functionality working correctly."
  - task: "Reviews allowed for connections (not only project teammates)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "POST /api/students/{sid}/reviews now allows reviews if shared project OR connected. GET /api/students can_review=true if teammate OR connected. Verified via curl: review after connect succeeds."
        - working: true
          agent: "testing"
          comment: "ROUND 2 testing completed. ✓ Hana initially cannot review George (non-teammate, non-connection) - correctly blocked with 403. ✓ After Hana and George connect, GET /api/students shows can_review=true and connection_status=connected for George. ✓ Hana successfully reviews George after connection - reputation recomputed correctly (reliability=85, avg_rating=4.0, review_count=1). ✓ Review for Diana (neither teammate nor connection) still correctly blocked with 403. All review-for-connections functionality working correctly."
  - task: "Projects owner connection_status field"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "GET /api/projects owner object includes connection_status field (self/none/pending_out/connected). Verified via curl: own project shows 'self', others show appropriate status."
        - working: true
          agent: "testing"
          comment: "ROUND 2 testing completed. ✓ GET /api/projects returns all projects with owner.connection_status field. ✓ All connection_status values are valid (self/none/pending_out/pending_in/connected). ✓ Alice's own project correctly shows connection_status='self'. ✓ Projects owned by others show appropriate connection_status based on relationship. ✓ Connection status updates correctly after connecting to project owner. All project owner connection_status functionality working correctly."
  - task: "Smart Opportunities recommendation endpoint (GET /api/opportunities/recommended)"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Added GET /api/opportunities/recommended?limit=N — personalized ranked opportunities matched to skills/interests/looking_for + home area (state-match boost) with per-item reason + score + area_match. Local scorer primary; optional Groq LLM refinement if GROQ_API_KEY set (empty now -> engine 'local'). Frontend: Dashboard 'For you' picks (reason + % match, still State/City filterable); Opportunity Board 'Recommended for you' top-3 section. Please test GET /api/opportunities/recommended returns {recommendations:[...], engine}; each item has score/reason/area_match/location; area-matched opps rank higher for alice@lincolnhs.edu."
        - working: true
          agent: "testing"
          comment: "Comprehensive testing completed - ALL TESTS PASSED ✅. (1) RESPONSE SHAPE: Returns {recommendations:[...], engine:'local'} as expected (GROQ_API_KEY empty). (2) FIELD VALIDATION: All recommendations include id, title, org, type, location, deadline, score (0-100 number), reason (non-empty string), area_match (boolean). (3) LIMIT PARAMETER: Correctly respects limit param (limit=5 returns <=5 items). (4) SORTING: Items sorted by score descending. (5) ALICE (Boston, MA): Gets 3 MA opportunities (MIT THINK Scholars, HackMIT 2026, Boston Startup Weekend) with area_match=true ranking in top 3 (all score=79). Reason mentions skills/interests + area. (6) DIANA (San Francisco, CA): Gets Bay Area Youth Robotics League with area_match=true ranking #1 (score=98). Personalization confirmed - different top results than Alice. (7) NEW USER (no skills/location): Still returns recommendations without error, all area_match=false. (8) UNAUTHENTICATED: Returns 401 as expected. (9) REGRESSION: GET /api/opportunities returns full list (10 items) with location; GET /api/dashboard still works. All requirements met perfectly."

frontend:
  - task: "Dashboard: Connections box, Find teammates -> Discover, location-scoped opportunities"
    implemented: true
    working: true
    file: "frontend/src/pages/Dashboard.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Screenshot-verified visually. Awaiting user go-ahead for automated frontend test."
        - working: true
          agent: "testing"
          comment: "ROUND 5 UI testing completed - ALL TESTS PASSED ✅. (1) DASHBOARD AREA DROPDOWNS: State dropdown contains all 51 U.S. states (50 states + DC) including California, New York, Texas, Massachusetts. Selected Texas → City dropdown correctly populated with 5 Texas cities (Austin, Houston, Dallas, San Antonio, Fort Worth). (2) DASHBOARD OPPORTUNITIES: Found 5 opportunity cards, all showing locations (e.g., 'Boston, MA') with MapPin icons. (3) CONNECTIONS BOX: Shows 2 connections stat, clickable to navigate to /app/connections. All dashboard functionality working correctly."
  - task: "Discover: Connect/accept buttons + Review modal; endorse removed"
    implemented: true
    working: true
    file: "frontend/src/pages/Discover.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "ReviewModal component added. Awaiting user go-ahead for automated frontend test."
        - working: true
          agent: "testing"
          comment: "ROUND 5 UI testing completed - ReviewModal functionality verified through Connections page testing. Modal opens correctly, displays all form elements (star rating 1-5, reliability slider, comment box, submit button), and successfully submits reviews. Review appears in the list after submission. No endorse functionality present (correctly removed)."
  - task: "Connections page + nav; Profile location field"
    implemented: true
    working: true
    file: "frontend/src/pages/Connections.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "New /app/connections route + nav item. Profile location input added."
        - working: true
          agent: "testing"
          comment: "ROUND 5 UI testing completed - ALL TESTS PASSED ✅. (1) CONNECTIONS PAGE: Successfully navigated to /app/connections, found 2 connections (Diana Park, Ethan Wright). (2) REVIEW MODAL (THE REPORTED BUG - NOW FIXED): Clicked star button on Diana Park's connection card → Review modal appeared successfully (data-testid='review-modal'). Modal shows 'Collaborator reviews' title, 'Leave a review' form with all required elements: star rating (1-5) ✅, reliability slider (90% default) ✅, comment box ✅, submit button ✅. (3) REVIEW SUBMISSION: Successfully submitted 4-star review with comment 'Great collaboration! Very reliable teammate.' Review appeared in modal list (1 review item visible). Bug is FIXED - review modal opens and works correctly from Connections page."
  - task: "Area dropdowns with ALL U.S. states and cities (Dashboard + Opportunity Board)"
    implemented: true
    working: true
    file: "frontend/src/components/AreaSelect.js, frontend/src/constants/locations.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "ROUND 5 UI testing completed - ALL TESTS PASSED ✅. (1) DASHBOARD AREA DROPDOWNS: State dropdown (data-testid='opp-state-select') contains 51 states (50 states + DC) including California, New York, Texas, Massachusetts. Selected Texas → City dropdown (data-testid='opp-city-select') populated with 5 Texas cities (Austin, Houston, Dallas, San Antonio, Fort Worth). (2) OPPORTUNITY BOARD AREA DROPDOWNS: State dropdown (data-testid='oppboard-state-select') contains 51 states including California, New York, Texas, Massachusetts. Selected Texas → City dropdown (data-testid='oppboard-city-select') populated with 5 Texas cities (Austin, Houston, Dallas, San Antonio, Fort Worth). Enhancement is WORKING - all U.S. states and cities are populated correctly from src/constants/locations.js."
  - task: "Opportunity locations shown on cards with pin icons"
    implemented: true
    working: true
    file: "frontend/src/pages/Opportunities.js, frontend/src/pages/Dashboard.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "ROUND 5 UI testing completed - ALL TESTS PASSED ✅. (1) OPPORTUNITY BOARD RECOMMENDED: Found 3 recommended opportunity cards, all showing locations (e.g., 'Cambridge, MA') with MapPin icons. (2) OPPORTUNITY BOARD BROWSE ALL: Found 20 browse all opportunity cards, all showing locations (e.g., 'Boston Startup Weekend for Teens', 'Boston, MA', 'Chicago, IL', 'San Francisco, CA') with MapPin icons. (3) DASHBOARD OPPORTUNITIES: Found 5 opportunity cards, all showing locations (e.g., 'Boston, MA') with MapPin icons. All opportunity cards correctly display locations with pin icons as required."

metadata:
  created_by: "main_agent"
  version: "1.3"
  test_sequence: 5
  run_ui: true

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "Implemented reviews + connections + location-scoped opportunities and removed endorse. Recreated missing .env files (app was fully down). Please test the backend endpoints."
    - agent: "testing"
      message: "All backend tests PASSED: reviews (gating/upsert/reputation recompute), connections (send/accept/decline/auto-accept/self-block), endorse removed (404), reputation has no endorsements, opportunities include location, profile location persists."
    - agent: "main"
      message: "ROUND 2 changes to test: (1) Messaging limit: a user who is NOT connected to the recipient can send only ONE message; the 2nd POST /api/messages returns 403. GET /api/messages/{id} now returns object {messages, connected, can_send}. Connected users have no limit. (2) Reviews now allowed for CONNECTED users too (not only project mates): can_review true if shared project OR accepted connection; POST review succeeds for a connection. (3) GET /api/projects owner object now has connection_status (self/none/pending_out/connected). Please retest these three areas plus regression on reviews/connections. Verified via curl already: stranger 1-msg limit (200 then 403), review after connect works, project owner status present."
    - agent: "testing"
      message: "ROUND 2 PASSED: messaging 1-msg stranger limit + object response, reviews for connections, project owner connection_status, dashboard regression."
    - agent: "main"
      message: "ROUND 3 (frontend-only, no backend change): Area selection split into State + City dropdowns (profile via AreaPicker, dashboard + opportunity board filters via AreaFilter, dataset in src/constants/locations.js). Location still stored as 'City, ST' string via existing PUT /api/profile. Added leave/see-reviews from Connections page (ReviewModal, can_review forced true since connected). Verified visually via screenshots: profile State/City prefilled (Massachusetts/Boston), connections review modal opens, area filters render. No backend retest needed."
    - agent: "main"
      message: "ROUND 5 (bug fix + enhancement): (1) AreaFilter (Dashboard 'For you' + Opportunity Board) now populated with ALL 50 U.S. states + DC and their cities from src/constants/locations.js (no longer derived from opportunities). (2) Opportunity locations shown on cards (board recommended + browse-all + dashboard) — already present, confirmed. (3) Connections page star button opens the ReviewModal to leave/see reviews — verified opens in preview via normal + forced click; user was likely on a stale build. Frontend restarted + recompiled. Requesting frontend UI verification of: connections review popup opens & submits; area dropdowns list all US states/cities; opportunity cards show location."
    - agent: "testing"
      message: "Backend testing completed - ALL TESTS PASSED ✅. Tested all 3 high-priority backend tasks: (1) Reviews API - all functionality working including shared-project gating, reputation recompute, upsert behavior, self-review prevention. (2) Connections API - full lifecycle working including send/accept/decline, auto-accept, duplicate handling, dashboard stats. (3) Regression - endorse endpoint removed (404), reputation without endorsements, opportunities with location, profile location persists. All backend APIs are functioning correctly as per requirements. Ready for main agent to summarize and finish."
    - agent: "testing"
      message: "ROUND 2 backend testing completed - ALL TESTS PASSED ✅. Comprehensive testing of three new features: (1) MESSAGING LIMIT FOR STRANGERS - First message succeeds, second returns 403 with appropriate error. GET /api/messages/{id} returns correct object structure {messages, connected, can_send}. After connecting, unlimited messages work. (2) REVIEWS ALLOWED FOR CONNECTIONS - Non-connected users cannot review (403). After connecting, can_review=true and review succeeds. Reputation recomputes correctly. Reviews for non-teammates/non-connections still blocked. (3) PROJECTS OWNER CONNECTION_STATUS - All projects include owner.connection_status field with valid values (self/none/pending_out/connected). Own projects show 'self'. Status updates correctly after connecting. DASHBOARD REGRESSION - stats.connections and stats.connection_requests present, all opportunities include location field. All backend APIs functioning correctly. Ready for main agent to summarize and finish."
    - agent: "testing"
      message: "ROUND 4 (Smart Opportunities) backend testing completed - ALL TESTS PASSED ✅. Comprehensive testing of GET /api/opportunities/recommended endpoint: (1) AUTHENTICATION - Unauthenticated requests correctly return 401. (2) RESPONSE STRUCTURE - Returns {recommendations:[...], engine:'local'} with all required fields (id, title, org, type, location, deadline, score 0-100, reason non-empty string, area_match boolean). (3) PERSONALIZATION - Alice (Boston, MA) gets 3 MA opportunities (MIT THINK, HackMIT, Boston Startup Weekend) with area_match=true in top 3 (score=79). Diana (San Francisco, CA) gets Bay Area Youth Robotics League with area_match=true ranking #1 (score=98). Different top results confirm personalization works. (4) EDGE CASES - New user with no skills/location still gets recommendations (area_match=false for all). Limit parameter works correctly (limit=5 returns <=5 items). Items sorted by score descending. (5) REGRESSION - GET /api/opportunities returns full list (10 items) with location. GET /api/dashboard still works. All requirements met perfectly. Ready for main agent to summarize and finish."
    - agent: "testing"
      message: "ROUND 5 FRONTEND UI testing completed - ALL TESTS PASSED ✅. Comprehensive testing of three user-reported items: (1) CONNECTIONS REVIEW MODAL (BUG FIX): Successfully navigated to /app/connections, found 2 connections. Clicked star button on Diana Park's connection card → Review modal appeared with data-testid='review-modal'. Modal displays 'Collaborator reviews' title and 'Leave a review' form with all required elements: star rating (1-5), reliability slider (90% default), comment box, submit button. Successfully submitted 4-star review with comment. Review appeared in modal list. BUG IS FIXED ✅. (2) AREA DROPDOWNS WITH ALL U.S. STATES (ENHANCEMENT): Dashboard State dropdown (data-testid='opp-state-select') contains 51 states (50 + DC) including California, New York, Texas, Massachusetts. Selected Texas → City dropdown populated with 5 Texas cities (Austin, Houston, Dallas, San Antonio, Fort Worth). Opportunity Board State dropdown (data-testid='oppboard-state-select') contains 51 states. Selected Texas → City dropdown populated correctly. ENHANCEMENT WORKING ✅. (3) OPPORTUNITY LOCATIONS ON CARDS: Opportunity Board Recommended section (3 cards) shows locations (e.g., 'Cambridge, MA') with MapPin icons. Browse All section (20 cards) shows locations with MapPin icons. Dashboard opportunities (5 cards) show locations (e.g., 'Boston, MA') with MapPin icons. ALL LOCATIONS VISIBLE ✅. Console shows only 2 non-critical 401 errors for /api/auth/me (pre-login). No critical errors. All three user-reported items are working correctly."

