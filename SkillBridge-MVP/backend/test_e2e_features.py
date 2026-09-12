import sys
import os

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from backend.main import app
import backend.database as database

import time
client = TestClient(app)

def run_tests():
    ts = int(time.time())
    student_email = f"jordan.{ts}@example.com"
    ind_email = f"techcorp.{ts}@example.com"

    print("--- 1. Testing Registration with Age & Gender ---")
    reg_payload = {
        "name": "Jordan Lee",
        "email": student_email,
        "password": "SecurePassword123!",
        "role": "student",
        "age": 22,
        "gender": "Female"
    }

    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code in (200, 201), f"Reg failed: {res.text}"
    data = res.json()
    assert data["user"]["age"] == 22, f"Expected age 22, got {data['user'].get('age')}"
    assert data["user"]["gender"] == "Female", f"Expected gender Female, got {data['user'].get('gender')}"
    print("Student registered successfully with demographics: Age 22, Gender Female")

    print("\n--- 2. Testing Login & Profile Retrieval ---")
    login_res = client.post("/api/auth/login", json={"email": student_email, "password": "SecurePassword123!"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    student_token = login_res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    prof_res = client.get("/api/student/profile", headers=student_headers)
    assert prof_res.status_code == 200, f"Profile failed: {prof_res.text}"
    prof = prof_res.json()
    assert prof["age"] == 22
    assert prof["gender"] == "Female"
    assert "gamification" in prof
    print("Student profile validated with demographics & gamification profile")

    print("\n--- 3. Testing Industry Registration & Opportunity Creation ---")
    ind_payload = {
        "name": "TechCorp Recruiter",
        "email": ind_email,
        "password": "SecurePassword123!",
        "role": "industry",
        "age": 30,
        "gender": "Prefer not to say"
    }
    reg_ind = client.post("/api/auth/register", json=ind_payload)
    assert reg_ind.status_code in (200, 201), f"Ind reg failed: {reg_ind.text}"
    ind_login = client.post("/api/auth/login", json={"email": ind_email, "password": "SecurePassword123!"})
    ind_token = ind_login.json()["access_token"]
    ind_headers = {"Authorization": f"Bearer {ind_token}"}

    database.seed_default_skills()
    skills = database.get_all_skills()
    first_skill_id = skills[0]["id"]

    # Post an opportunity
    opp_res = client.post("/api/opportunities", headers=ind_headers, json={
        "title": "Cloud Systems Engineer",
        "company_name": "TechCorp Global",
        "description": "Building scalable cloud native pipelines.",
        "required_skills": [
            {"skill_id": first_skill_id, "required_score": 70}
        ]
    })
    assert opp_res.status_code in (200, 201), f"Opp creation failed: {opp_res.text}"
    opp_data = opp_res.json()
    opp = opp_data.get("opportunity", opp_data)
    opp_id = opp["id"]
    print(f"Created Opportunity #{opp_id}: {opp['title']}")

    print("\n--- 4. Industry Configures Company Screening Test ---")
    screening_payload = {
        "title": "Cloud Systems Technical Screening",
        "description": "Verify core Python and networking concepts.",
        "passing_score": 75,
        "time_limit_minutes": 25,
        "questions": [
            {
                "question_text": "What is the primary benefit of connection pooling in database clients?",
                "option_a": "Encrypts all SQL queries",
                "option_b": "Reuses open socket connections to eliminate handshake overhead",
                "option_c": "Converts SQLite databases into distributed clusters",
                "option_d": "Eliminates memory usage",
                "correct_answer": "b",
                "explanation": "Connection pooling avoids repetitive TCP and TLS handshake latency."
            },
            {
                "question_text": "In Python, which keyword creates an asynchronous generator?",
                "option_a": "async def with yield",
                "option_b": "def with await",
                "option_c": "lambda with async",
                "option_d": "async for without def",
                "correct_answer": "a",
                "explanation": "async def with yield defines an async generator."
            }
        ]
    }
    st_res = client.post(f"/api/opportunities/{opp_id}/screening-test", headers=ind_headers, json=screening_payload)
    assert st_res.status_code in (200, 201), f"Failed to set screening test: {st_res.text}"
    test_id = st_res.json()["test"]["id"]
    print(f"Screening test #{test_id} created with {len(st_res.json()['test']['questions'])} questions")

    # Verify answers hidden for student
    st_get_student = client.get(f"/api/opportunities/{opp_id}/screening-test", headers=student_headers)
    assert st_get_student.status_code == 200
    q0 = st_get_student.json()["test"]["questions"][0]
    assert q0.get("correct_answer") is None, "Correct answer should NOT be exposed to student!"
    print("Verified: Answer keys are safely hidden from students")

    print("\n--- 5. Student Applies & Takes Screening Test ---")
    apply_res = client.post(f"/api/opportunities/{opp_id}/apply", headers=student_headers)
    assert apply_res.status_code in (200, 201), f"Application failed: {apply_res.text}"

    # Check student applications before test
    apps_res = client.get("/api/student/applications", headers=student_headers)
    assert apps_res.status_code == 200
    apps_data = apps_res.json()
    app_list = apps_data if isinstance(apps_data, list) else apps_data.get("applications", [])
    my_app = next(a for a in app_list if a["opportunity_id"] == opp_id)
    assert my_app["screening_test_id"] == test_id
    assert my_app["screening"] is None
    print("Application shows pending screening test")

    # Student submits screening answers
    q_ids = [str(q["id"]) for q in st_get_student.json()["test"]["questions"]]
    submit_payload = {
        "answers": {
            q_ids[0]: "b",
            q_ids[1]: "a"
        }
    }
    sub_res = client.post(f"/api/screening-tests/{test_id}/submit", headers=student_headers, json=submit_payload)
    assert sub_res.status_code == 200, f"Submit failed: {sub_res.text}"
    result = sub_res.json()
    assert result["score"] == 100.0, f"Expected 100% score, got {result['score']}"
    assert result["passed"] is True
    assert result["xp_awarded"] == 50
    assert "screening_star" in result["new_badges"]
    print("Student scored 100%, passed screening, earned +50 XP and unlocked 'screening_star' badge!")

    # Verify student applications table now shows screening results
    apps_after_res = client.get("/api/student/applications", headers=student_headers)
    apps_after_data = apps_after_res.json()
    app_after_list = apps_after_data if isinstance(apps_after_data, list) else apps_after_data.get("applications", [])
    my_app_after = next(a for a in app_after_list if a["opportunity_id"] == opp_id)
    assert my_app_after["screening"]["score"] == 100.0
    assert my_app_after["screening"]["passed"] is True
    print("Student applications view now confirms passed screening test")

    print("\n--- 6. Industry Recruiter Evaluates Applicant with Screening & Demographics ---")
    applicants_res = client.get(f"/api/industry/opportunities/{opp_id}/applicants", headers=ind_headers)
    assert applicants_res.status_code == 200, f"Applicants failed: {applicants_res.text}"
    applicants = applicants_res.json()["applicants"]
    assert len(applicants) >= 1
    candidate = next(a for a in applicants if a["email"] == student_email)
    assert candidate["age"] == 22, f"Expected age 22, got {candidate.get('age')}"
    assert candidate["gender"] == "Female", f"Expected gender Female, got {candidate.get('gender')}"
    assert candidate["screening"] is not None
    assert candidate["screening"]["score"] == 100.0
    assert candidate["screening"]["passed"] is True
    print(f"Recruiter verified applicant: {candidate['name']}, Age {candidate['age']}, Gender {candidate['gender']}, Screening: {candidate['screening']['score']}% (Passed)")

    # Recruiter shortlists candidate
    app_id = candidate["application_id"]
    status_res = client.patch(f"/api/applications/{app_id}/status", headers=ind_headers, json={"status": "shortlisted"})
    assert status_res.status_code == 200
    print(f"Application #{app_id} status updated to 'shortlisted' successfully!")

    print("\n==========================================")
    print("ALL END-TO-END FEATURE TESTS PASSED! (6/6)")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
