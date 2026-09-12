# backend/main.py
#
# WHAT THIS FILE DOES:
# This file is the primary web server and router for SkillBridge.
# It uses FastAPI to:
#   1. Initialize database and seed MVP skills on startup
#   2. Serve HTML web pages (Home, Roles, Student Dashboard, Assessment, Login, Register)
#   3. Expose REST APIs for Database Health, Skills CRUD, Authentication (Stage 3),
#      and Student Assessment & Skill Profiles (Stage 4)
#   4. Validate all incoming user data and enforce role-based access control

import mimetypes
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Any, Union

# Import database functions
from backend.database import (
    init_db,
    seed_default_skills,
    get_all_skills,
    get_skill_by_id,
    get_skill_by_name,
    create_skill,
    update_skill,
    delete_skill,
    get_database_health,
    get_foreign_key_relationships,
    create_user,
    get_user_by_email,
    get_student_skills,
    save_or_update_student_skill,
    create_opportunity,
    get_opportunity,
    get_opportunities,
    create_application,
    get_student_applications,
    get_opportunity_applicants,
    update_application_status,
    get_institution_statistics,
    get_student_gamification_profile,
    get_leaderboard_data,
    update_student_streak,
    record_xp_activity,
    evaluate_and_award_badges,
    get_all_badges,
    seed_demo_leaderboard_data,
    create_or_update_screening_test,
    get_screening_test_by_opportunity,
    get_screening_test_by_id,
    record_screening_attempt,
    get_student_screening_attempt,
)

# Import security and authentication functions
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

# Import assessment logic (Stage 4)
from backend.assessment import (
    get_assessment_questions,
    evaluate_assessment_answers
)
from backend.matching import build_skill_gaps, calculate_match

# Initialize the FastAPI web application
app = FastAPI(
    title="SkillBridge API",
    description="Backend API for SkillBridge - Academia-Industry Collaboration Portal",
    version="0.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema and ensure default MVP skills and demo leaderboard exist
init_db()
seed_default_skills()
seed_demo_leaderboard_data()


@app.get("/api/healthz")
def healthz():
    """Lightweight readiness endpoint used by the managed API service."""
    return {"status": "ok"}


# ---------------------------------------------------------
# CUSTOM VALIDATION ERROR HANDLER
# ---------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    msg = first_error.get("msg", "Invalid input data.")
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": msg}
    )


# =========================================================
# INPUT VALIDATION SCHEMAS (Pydantic Models)
# =========================================================

class SkillInput(BaseModel):
    name: str = Field(..., description="The name of the skill, e.g. 'Python'")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Skill name cannot be empty or whitespace only.")
        if len(clean) > 100:
            raise ValueError("Skill name cannot exceed 100 characters.")
        return clean


class UserRegisterInput(BaseModel):
    name: str = Field(..., description="Full display name")
    email: str = Field(..., description="Valid unique email address")
    password: str = Field(..., description="Password (minimum 6 characters)")
    role: str = Field(..., description="Role: student, industry, academician, or institution")
    age: Optional[int] = Field(None, description="Age (14 to 100)")
    gender: Optional[str] = Field(None, description="Gender (Male, Female, Other, Prefer not to say)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Name cannot be empty.")
        if len(clean) > 100:
            raise ValueError("Name cannot exceed 100 characters.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        clean = value.strip().lower()
        if not clean:
            raise ValueError("Email cannot be empty.")
        if "@" not in clean or "." not in clean.split("@")[-1] or len(clean) < 5:
            raise ValueError("Please provide a valid email address (e.g. user@example.com).")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if len(value) > 128:
            raise ValueError("Password cannot exceed 128 characters.")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        clean = value.strip().lower()
        allowed = ("student", "industry", "academician", "institution")
        if clean not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(allowed)}.")
        return clean

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and (value < 14 or value > 100):
            raise ValueError("Age must be between 14 and 100.")
        return value

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value.strip():
            clean = value.strip().title()
            allowed = {"Male", "Female", "Other", "Prefer Not To Say"}
            if clean not in allowed:
                raise ValueError(f"Gender must be one of: {', '.join(sorted(allowed))}.")
            return clean
        return None


class UserLoginInput(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        clean = value.strip().lower()
        if not clean:
            raise ValueError("Email cannot be empty.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value:
            raise ValueError("Password cannot be empty.")
        return value




class ScreeningQuestionInput(BaseModel):
    question_text: str = Field(..., min_length=3, description="Question prompt")
    options: list[str] = Field(default_factory=list, description="List of 2-6 multiple choice options")
    correct_option: int = Field(0, ge=0, description="0-indexed integer of the correct option")
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_question_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If options list is not provided, populate from option_a, option_b, etc.
            if not data.get("options") and (data.get("option_a") or data.get("option_b")):
                opts = []
                for key in ["option_a", "option_b", "option_c", "option_d"]:
                    if data.get(key):
                        opts.append(str(data[key]).strip())
                data["options"] = opts

            # If correct_answer ("a", "b", etc.) is given, map to correct_option index
            if "correct_option" not in data and data.get("correct_answer"):
                ca = str(data["correct_answer"]).strip().lower()
                char_map = {"a": 0, "b": 1, "c": 2, "d": 3}
                data["correct_option"] = char_map.get(ca, 0)
        return data

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        cleaned = [o.strip() for o in value if o.strip()]
        if len(cleaned) < 2:
            raise ValueError("Each question must provide at least 2 non-empty options.")
        return cleaned

    @model_validator(mode="after")
    def validate_correct_index(self):
        if self.correct_option >= len(self.options):
            raise ValueError(f"correct_option ({self.correct_option}) is out of range for {len(self.options)} options.")
        return self


class ScreeningTestCreateInput(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, description="Title of the screening test")
    description: Optional[str] = Field(None, max_length=500, description="Test description or instructions")
    passing_score: int = Field(60, ge=10, le=100, description="Minimum score (percentage) required to pass")
    time_limit_minutes: Optional[int] = Field(20, ge=5, le=180, description="Time limit in minutes")
    questions: list[ScreeningQuestionInput] = Field(..., min_length=1, description="List of screening test questions")


class ScreeningSubmissionInput(BaseModel):
    answers: dict[str, Any] = Field(..., description="Mapping of question ID string to selected option index or letter key")

    @field_validator("answers")
    @classmethod
    def normalize_submission_answers(cls, val: dict) -> dict:
        char_map = {"a": 0, "b": 1, "c": 2, "d": 3}
        normalized = {}
        for qid, ans in val.items():
            if isinstance(ans, str) and ans.lower() in char_map:
                normalized[str(qid)] = char_map[ans.lower()]
            else:
                try:
                    normalized[str(qid)] = int(ans)
                except (ValueError, TypeError):
                    normalized[str(qid)] = 0
        return normalized

class AssessmentSubmissionInput(BaseModel):
    answers: dict = Field(..., description="Mapping of question ID to selected option index")

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, value: dict) -> dict:
        if not value:
            raise ValueError("Assessment answers cannot be empty.")
        validated = {}
        for qid_raw, opt_raw in value.items():
            try:
                qid = int(qid_raw)
                opt = int(opt_raw)
                if opt < 0 or opt > 3:
                    raise ValueError(f"Option index for question {qid} must be between 0 and 3.")
                validated[qid] = opt
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid answer format for question '{qid_raw}': {str(e)}")
        return validated


class OpportunitySkillInput(BaseModel):
    skill_id: int = Field(..., gt=0, description="ID from the shared skills catalog")
    required_score: int = Field(50, ge=0, le=100)
    minimum_score: Optional[int] = Field(None, ge=0, le=100)

    @model_validator(mode="after")
    def use_minimum_score_alias(self):
        if self.minimum_score is not None:
            self.required_score = self.minimum_score
        return self


class OpportunityInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field("", max_length=3000)
    company_name: str = Field(..., min_length=1, max_length=150)
    required_skills: list[OpportunitySkillInput] = Field(..., min_length=1, max_length=4)

    @field_validator("title", "company_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("Title and company name cannot be empty.")
        return clean

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()


class ApplicationStatusInput(BaseModel):
    status: str = Field(..., description="applied, shortlisted, rejected, or accepted")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        clean = value.strip().lower()
        if clean not in {"applied", "shortlisted", "rejected", "accepted"}:
            raise ValueError("Status must be applied, shortlisted, rejected, or accepted.")
        return clean


# =========================================================
# STAGE 4: STUDENT ASSESSMENT & SKILL PROFILE ENDPOINTS
# =========================================================

@app.get("/api/assessment")
def get_assessment():
    """
    STAGE 4: Returns the 12 multiple-choice questions for the skill assessment.
    
    SECURITY:
    Does NOT return correct answers to prevent frontend cheating.
    """
    return get_assessment_questions()


@app.post("/api/assessment/submit")
def submit_assessment(
    submission: AssessmentSubmissionInput,
    current_user: dict = Depends(get_current_user)
):
    """
    STAGE 4: Evaluates student answers on the server, calculates normalized
    scores (0 - 100%), and saves them into the student_skills table.
    
    SECURITY RULES ENFORCED:
    1. Only authenticated students can submit (role == 'student').
    2. Student ID comes strictly from the verified JWT (never from client body).
    3. Retaking the assessment updates existing scores rather than inserting duplicates.
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students are permitted to take and submit skill assessments."
        )

    # Ensure default skills are present in database
    seed_default_skills()

    # Server calculates the scores
    scores_by_skill = evaluate_assessment_answers(submission.answers)

    student_id = current_user["id"]
    updated_skills = []

    for skill_name, score in scores_by_skill.items():
        # Get or create skill entry in skills table
        skill_record = get_skill_by_name(skill_name)
        if not skill_record:
            skill_record = create_skill(skill_name)

        skill_id = skill_record["id"]
        # Save or update score in student_skills
        save_or_update_student_skill(student_id, skill_id, score)

        updated_skills.append({
            "skill_id": skill_id,
            "skill_name": skill_name,
            "score": score
        })

    # Gamification: Award XP, update streak, evaluate badges
    avg_score = sum(scores_by_skill.values()) / max(len(scores_by_skill), 1)
    earned_xp = int(75 + (avg_score * 0.5))
    record_xp_activity(
        student_id,
        "assessment_completed",
        earned_xp,
        f"Completed Skill Assessment (Score: {round(avg_score)}%)"
    )
    update_student_streak(student_id)
    new_badges = evaluate_and_award_badges(student_id)
    gamification_summary = get_student_gamification_profile(student_id)

    return {
        "message": "Assessment evaluated and skill profile updated successfully.",
        "student_id": student_id,
        "skills": updated_skills,
        "gamification": {
            "xp_earned": earned_xp,
            "new_badges": new_badges,
            "total_xp": gamification_summary["xp"],
            "level": gamification_summary["level"],
            "level_title": gamification_summary["level_title"],
            "streak": gamification_summary["streak"],
        }
    }


@app.get("/api/student/profile")
def get_student_profile(current_user: dict = Depends(get_current_user)):
    """
    STAGE 4: Returns the logged-in student's profile, assessed skill scores, and gamification state.
    
    SECURITY RULES ENFORCED:
    1. Requires valid JWT Bearer token.
    2. Restricted to students only (role == 'student').
    3. Student ID is derived strictly from the token; clients cannot pass another ID.
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students have access to student skill profiles."
        )

    skills = get_student_skills(current_user["id"])
    skill_gaps = build_skill_gaps(skills)
    overall_readiness = round(
        sum(skill["score"] for skill in skills) / len(skills)
    ) if skills else 0
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "age": current_user.get("age"),
        "gender": current_user.get("gender"),
        "has_taken_assessment": len(skills) > 0,
        "skills": skills,
        "skill_gaps": skill_gaps,
        "overall_readiness": overall_readiness,
        "applications": get_student_applications(current_user["id"]),
        "gamification": get_student_gamification_profile(current_user["id"]),
    }


# =========================================================
# MVP SKILL GAPS, OPPORTUNITIES, MATCHING & APPLICATIONS
# =========================================================

def _student_opportunity_view(opportunity: dict, student_id: int) -> dict:
    skills = get_student_skills(student_id)
    return {
        **opportunity,
        **calculate_match(opportunity.get("required_skills", []), skills),
    }


def _require_role(current_user: dict, allowed_roles: set, message: str):
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
        )


@app.get("/api/student/skill-gaps")
def get_student_skill_gaps(current_user: dict = Depends(get_current_user)):
    """Return explainable gap labels based on the logged-in student's scores."""
    _require_role(
        current_user,
        {"student"},
        "Only students have access to skill-gap analysis.",
    )
    skills = get_student_skills(current_user["id"])
    return {
        "overall_readiness": round(
            sum(skill["score"] for skill in skills) / len(skills)
        ) if skills else 0,
        "skill_gaps": build_skill_gaps(skills),
    }


@app.get("/api/opportunities")
def list_recommended_opportunities(
    current_user: dict = Depends(get_current_user),
):
    """List real opportunities with a match score for the current student."""
    _require_role(
        current_user,
        {"student"},
        "Only students can browse recommended internships.",
    )
    return [
        _student_opportunity_view(opportunity, current_user["id"])
        for opportunity in get_opportunities()
    ]


@app.get("/api/opportunities/mine")
def list_my_opportunities(current_user: dict = Depends(get_current_user)):
    _require_role(
        current_user,
        {"industry"},
        "Only industry users can view their posted opportunities.",
    )
    return get_opportunities(industry_id=current_user["id"])


@app.post("/api/opportunities", status_code=status.HTTP_201_CREATED)
def post_opportunity(
    opportunity_data: OpportunityInput,
    current_user: dict = Depends(get_current_user),
):
    _require_role(
        current_user,
        {"industry"},
        "Only industry users can create internship opportunities.",
    )
    try:
        return create_opportunity(
            industry_id=current_user["id"],
            title=opportunity_data.title,
            description=opportunity_data.description,
            company_name=opportunity_data.company_name,
            required_skills=[
                {
                    "skill_id": skill.skill_id,
                    "required_score": skill.required_score,
                }
                for skill in opportunity_data.required_skills
            ],
        )
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@app.get("/api/opportunities/{opportunity_id}")
def opportunity_detail(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
):
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )
    if current_user.get("role") == "student":
        return _student_opportunity_view(opportunity, current_user["id"])
    if (
        current_user.get("role") == "industry"
        and opportunity["industry_id"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own opportunity details.",
        )
    return opportunity


@app.post("/api/opportunities/{opportunity_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_to_opportunity(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
):
    _require_role(
        current_user,
        {"student"},
        "Only students can apply to internships.",
    )
    try:
        application = create_application(current_user["id"], opportunity_id)
        # Gamification: Award XP (+30 XP), update streak, evaluate badges
        record_xp_activity(
            current_user["id"],
            "opportunity_applied",
            30,
            f"Applied to opportunity #{opportunity_id}"
        )
        update_student_streak(current_user["id"])
        evaluate_and_award_badges(current_user["id"])

        return {
            "message": "Application submitted successfully.",
            "application": application,
        }
    except ValueError as error:
        detail = str(error)
        code = (
            status.HTTP_409_CONFLICT
            if "already applied" in detail.lower()
            else status.HTTP_404_NOT_FOUND
            if "not found" in detail.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail)


@app.get("/api/student/applications")
def list_student_applications(current_user: dict = Depends(get_current_user)):
    _require_role(
        current_user,
        {"student"},
        "Only students can view their applications.",
    )
    return get_student_applications(current_user["id"])


@app.get("/api/industry/opportunities/{opportunity_id}/applicants")
def list_opportunity_applicants(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
):
    _require_role(
        current_user,
        {"industry"},
        "Only industry users can view applicants.",
    )
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )
    if opportunity["industry_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view applicants for your own opportunities.",
        )

    applicants = []
    for applicant in get_opportunity_applicants(opportunity_id):
        skills = get_student_skills(applicant["student_id"])
        applicants.append({
            **applicant,
            "skills": skills,
            **calculate_match(opportunity["required_skills"], skills),
        })
    return {
        "opportunity": opportunity,
        "applicants": applicants,
    }


@app.patch("/api/applications/{application_id}/status")
@app.put("/api/applications/{application_id}/status")
def change_application_status(
    application_id: int,
    status_data: ApplicationStatusInput,
    current_user: dict = Depends(get_current_user),
):
    _require_role(
        current_user,
        {"industry"},
        "Only industry users can update application status.",
    )
    updated = update_application_status(
        application_id=application_id,
        industry_id=current_user["id"],
        new_status=status_data.status,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found for one of your opportunities.",
        )
    return {
        "message": "Application status updated successfully.",
        "application": updated,
    }


@app.get("/api/institution/stats")
def institution_statistics(current_user: dict = Depends(get_current_user)):
    _require_role(
        current_user,
        {"academician", "institution"},
        "Only academicians and institutions can view readiness statistics.",
    )
    return get_institution_statistics()


# =========================================================
# INDUSTRY SCREENING TESTS API
# =========================================================

def _format_screening_test_response(test: dict) -> dict:
    if not test:
        return test
    formatted = dict(test)
    q_list = []
    for q in test.get("questions", []):
        q_copy = dict(q)
        opts = q.get("options", [])
        q_copy["option_a"] = opts[0] if len(opts) > 0 else ""
        q_copy["option_b"] = opts[1] if len(opts) > 1 else ""
        q_copy["option_c"] = opts[2] if len(opts) > 2 else ""
        q_copy["option_d"] = opts[3] if len(opts) > 3 else ""
        q_list.append(q_copy)
    formatted["questions"] = q_list
    formatted["time_limit_minutes"] = test.get("time_limit_minutes", 20)
    return formatted


@app.post("/api/opportunities/{opportunity_id}/screening-test")
def create_screening_test_endpoint(
    opportunity_id: int,
    data: ScreeningTestCreateInput,
    current_user: dict = Depends(get_current_user),
):
    _require_role(current_user, {"industry"}, "Only industry recruiters can create screening tests.")
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    if opportunity["industry_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only configure tests for your own opportunities.")

    questions_list = [q.model_dump() for q in data.questions]
    try:
        created = create_or_update_screening_test(
            opportunity_id=opportunity_id,
            title=data.title,
            description=data.description or "",
            passing_score=data.passing_score,
            questions=questions_list,
        )
        formatted = _format_screening_test_response(created)
        return {"message": "Screening test configured successfully.", "test": formatted, "screening_test": formatted}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/api/opportunities/{opportunity_id}/screening-test")
def get_opportunity_screening_test_endpoint(
    opportunity_id: int,
    current_user: dict = Depends(get_current_user),
):
    opportunity = get_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    is_owner = (current_user.get("role") == "industry" and opportunity["industry_id"] == current_user["id"])
    test = get_screening_test_by_opportunity(opportunity_id, include_answers=is_owner)
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No screening test configured for this opportunity.")

    if current_user.get("role") == "student":
        attempt = get_student_screening_attempt(current_user["id"], test["id"])
        test["my_attempt"] = attempt

    formatted = _format_screening_test_response(test)
    return {
        "test": formatted,
        "screening_test": formatted,
        **formatted,
    }


@app.get("/api/screening-tests/{test_id}")
def get_screening_test_endpoint(
    test_id: int,
    current_user: dict = Depends(get_current_user),
):
    test = get_screening_test_by_id(test_id, include_answers=False)
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening test not found.")

    if current_user.get("role") == "student":
        attempt = get_student_screening_attempt(current_user["id"], test_id)
        test["my_attempt"] = attempt

    formatted = _format_screening_test_response(test)
    return {
        "test": formatted,
        "screening_test": formatted,
        **formatted,
    }


@app.post("/api/screening-tests/{test_id}/submit")
def submit_screening_test_endpoint(
    test_id: int,
    submission: ScreeningSubmissionInput,
    current_user: dict = Depends(get_current_user),
):
    _require_role(current_user, {"student"}, "Only students can take screening tests.")
    try:
        result = record_screening_attempt(test_id, current_user["id"], submission.answers)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to evaluate screening test: {str(e)}")


@app.get("/api/screening-tests/{test_id}/my-attempt")
def get_my_screening_attempt_endpoint(
    test_id: int,
    current_user: dict = Depends(get_current_user),
):
    _require_role(current_user, {"student"}, "Only students have screening test attempts.")
    attempt = get_student_screening_attempt(current_user["id"], test_id)
    if not attempt:
        return {"attempted": False, "attempt": None}
    return {"attempted": True, "attempt": attempt}


# =========================================================
# GAMIFICATION REST API (XP, STREAKS, BADGES & LEADERBOARD)
# =========================================================

@app.get("/api/gamification/profile")
def get_gamification_profile(current_user: dict = Depends(get_current_user)):
    """
    Returns the complete gamification profile (XP, level, streak, badges, recent activity).
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Gamification profile is only accessible to student accounts."
        )
    return get_student_gamification_profile(current_user["id"])


@app.get("/api/gamification/leaderboard")
def get_leaderboard(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """
    Returns the student leaderboard, podium (Top 3), and current user ranking.
    """
    student_id = current_user["id"] if current_user.get("role") == "student" else None
    return get_leaderboard_data(current_student_id=student_id, limit=limit)


@app.post("/api/gamification/checkin")
def student_checkin(current_user: dict = Depends(get_current_user)):
    """
    Daily streak check-in: increments daily streak and awards bonus XP.
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Daily check-in is only accessible to student accounts."
        )
    streak_info = update_student_streak(current_user["id"])
    new_badges = evaluate_and_award_badges(current_user["id"])
    profile = get_student_gamification_profile(current_user["id"])
    return {
        "message": "Daily check-in recorded! Streak maintained.",
        "streak": streak_info["streak"],
        "bonus_xp": streak_info["bonus_xp"],
        "total_xp": profile["xp"],
        "new_badges": new_badges,
    }


@app.get("/api/gamification/badges")
def list_badges():
    """
    Returns the catalog of all achievement badges in the platform.
    """
    return get_all_badges()


# =========================================================
# STAGE 3: AUTHENTICATION API ENDPOINTS
# =========================================================

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegisterInput):
    """
    STAGE 3: Registers a new user account.
    """
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{user_data.email}' already exists."
        )

    hashed = hash_password(user_data.password)

    try:
        new_user = create_user(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed,
            role=user_data.role,
            age=user_data.age,
            gender=user_data.gender
        )
        return {
            "message": "User registered successfully.",
            "user": new_user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@app.post("/api/auth/login")
def login_user(credentials: UserLoginInput):
    """
    STAGE 3: Authenticates a user and issues a JWT access token.
    """
    user = get_user_by_email(credentials.email)

    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        raise invalid_credentials_error

    if not verify_password(credentials.password, user["password_hash"]):
        raise invalid_credentials_error

    token = create_access_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"]
        }
    )

    # Automatic daily streak check-in for student logins
    if user["role"] == "student":
        try:
            update_student_streak(user["id"])
            evaluate_and_award_badges(user["id"])
        except Exception:
            pass

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "age": user.get("age"),
            "gender": user.get("gender")
        }
    }


@app.get("/api/auth/me")
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    STAGE 3: Protected endpoint returning the currently logged-in user's profile.
    """
    return current_user


# =========================================================
# STAGE 2: DATABASE DIAGNOSTIC ENDPOINTS
# =========================================================

@app.get("/api/health/database")
def health_database():
    """
    Diagnostic endpoint to verify database connectivity and table structure.
    """
    try:
        return get_database_health()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )


@app.get("/api/health/database/relationships")
def health_relationships():
    """
    Diagnostic endpoint to verify foreign-key configuration across all tables.
    """
    try:
        return get_foreign_key_relationships()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect database relationships: {str(e)}"
        )


# =========================================================
# STAGE 2: SKILLS CRUD API ENDPOINTS
# =========================================================

@app.get("/api/skills")
def list_skills():
    """
    READ: Returns a list of all skills registered in the database.
    """
    try:
        return get_all_skills()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve skills: {str(e)}"
        )


@app.post("/api/skills", status_code=status.HTTP_201_CREATED)
def add_skill(skill_data: SkillInput):
    """
    CREATE: Adds a new skill to the database.
    """
    try:
        return create_skill(skill_data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill: {str(e)}"
        )


@app.put("/api/skills/{skill_id}")
def modify_skill(skill_id: int, skill_data: SkillInput):
    """
    UPDATE: Modifies an existing skill's name.
    """
    if skill_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill ID must be a positive integer."
        )

    try:
        updated = update_skill(skill_id, skill_data.name)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID {skill_id} not found."
            )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(e)}"
        )


@app.delete("/api/skills/{skill_id}")
def remove_skill(skill_id: int):
    """
    DELETE: Deletes a skill from the database.
    """
    if skill_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill ID must be a positive integer."
        )

    try:
        deleted = delete_skill(skill_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID {skill_id} not found."
            )
        return {
            "message": "Skill deleted successfully.",
            "id": skill_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete skill: {str(e)}"
        )


# =========================================================
# FRONTEND PATHS & ASSET CONFIGURATION
# =========================================================

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
LEGACY_DIR = FRONTEND_DIR / "legacy"
STATIC_DIR = FRONTEND_DIR / "dist" / "public"
INDEX_FILE = STATIC_DIR / "index.html"


def _render_legacy_template(filename: str) -> HTMLResponse:
    template_path = LEGACY_DIR / filename
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content=f"<!DOCTYPE html><html><body><h2>Template not found</h2><p>{filename} could not be found in frontend/legacy.</p></body></html>",
        status_code=404,
    )


# =========================================================
# PROTOTYPE FRONTEND ROUTES (LEGACY)
# =========================================================

@app.get("/legacy/assessment", response_class=HTMLResponse)
def assessment_page():
    return _render_legacy_template("assessment.html")


@app.get("/legacy/student", response_class=HTMLResponse)
def student_dashboard():
    return _render_legacy_template("student_dashboard.html")


@app.get("/legacy/leaderboard", response_class=HTMLResponse)
def leaderboard_page():
    return _render_legacy_template("leaderboard.html")


@app.get("/legacy/industry", response_class=HTMLResponse)
def industry_dashboard():
    return _render_legacy_template("industry_dashboard.html")


@app.get("/legacy/institution", response_class=HTMLResponse)
def institution_dashboard():
    return _render_legacy_template("institution_dashboard.html")


@app.get("/legacy/register", response_class=HTMLResponse)
def register_page():
    return _render_legacy_template("register.html")


@app.get("/legacy/login", response_class=HTMLResponse)
def login_page():
    return _render_legacy_template("login.html")


@app.get("/legacy", response_class=HTMLResponse)
def home():
    return _render_legacy_template("home.html")


@app.get("/legacy/roles", response_class=HTMLResponse)
def roles():
    return _render_legacy_template("roles.html")


# =========================================================
# MODERN WEB UI (REACT + TAILWIND FROM FRONTEND)
# =========================================================

def _serve_spa():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE, media_type="text/html")
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head><title>SkillBridge Frontend</title></head>
        <body style="font-family: sans-serif; padding: 40px; text-align: center;">
            <h2>Frontend build not found</h2>
            <p>Please build the frontend at <code>frontend</code>.</p>
        </body>
        </html>
        """,
        status_code=500,
    )


@app.get("/favicon.svg", include_in_schema=False)
def serve_favicon():
    fav = STATIC_DIR / "favicon.svg"
    if fav.exists():
        return FileResponse(fav, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/robots.txt", include_in_schema=False)
def serve_robots():
    rob = STATIC_DIR / "robots.txt"
    if rob.exists():
        return FileResponse(rob, media_type="text/plain")
    raise HTTPException(status_code=404, detail="Robots.txt not found")


@app.get("/assets/{file_path:path}", include_in_schema=False)
def serve_asset(file_path: str):
    asset_file = (STATIC_DIR / "assets" / file_path).resolve()
    assets_root = (STATIC_DIR / "assets").resolve()
    if not str(asset_file).startswith(str(assets_root)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not asset_file.exists() or not asset_file.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type, _ = mimetypes.guess_type(str(asset_file))
    return FileResponse(asset_file, media_type=media_type)


@app.get("/leaderboard", include_in_schema=False)
def serve_leaderboard_direct():
    return leaderboard_page()


@app.get("/student-dashboard", include_in_schema=False)
def serve_student_direct():
    return student_dashboard()


@app.get("/", include_in_schema=False)
def serve_root():
    return _serve_spa()


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa_catchall(full_path: str):
    if (
        full_path.startswith("api/")
        or full_path == "api"
        or full_path.startswith("legacy")
        or full_path.startswith("docs")
        or full_path.startswith("openapi.json")
        or full_path.startswith("redoc")
    ):
        raise HTTPException(status_code=404, detail="Not Found")

    # Check if a static file exists directly in dist/public (e.g. icons, manifest)
    candidate_file = (STATIC_DIR / full_path).resolve()
    if str(candidate_file).startswith(str(STATIC_DIR.resolve())) and candidate_file.is_file():
        media_type, _ = mimetypes.guess_type(str(candidate_file))
        return FileResponse(candidate_file, media_type=media_type)

    return _serve_spa()