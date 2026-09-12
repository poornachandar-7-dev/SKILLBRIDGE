"""Transparent skill-gap and opportunity matching helpers for the MVP."""


def classify_skill(score: int) -> str:
    """Map a score to the simple, explainable readiness bands."""
    if score >= 80:
        return "Strong"
    if score >= 50:
        return "Developing"
    return "Needs Improvement"


def improvement_for(skill_name: str, score: int) -> str:
    if score >= 80:
        return f"Keep practicing {skill_name} through projects and advanced challenges."
    if score >= 50:
        return f"Build more {skill_name} projects to move from developing to strong."
    return f"Strengthen your {skill_name} fundamentals with guided practice and small projects."


def build_skill_gaps(skills: list) -> list:
    """Enrich real assessment scores with a readable status and next step."""
    return [
        {
            **skill,
            "status": classify_skill(skill["score"]),
            "improvement": improvement_for(skill["skill_name"], skill["score"]),
        }
        for skill in skills
    ]


def calculate_match(required_skills: list, student_skills: list) -> dict:
    """
    Compare current student scores with required minimums.

    Each skill contributes its score relative to its requirement, capped at
    100. The average is intentionally transparent and easy to explain in a
    demo; no fake or hard-coded match values are used.
    """
    score_by_name = {
        skill["skill_name"].strip().lower(): int(skill["score"])
        for skill in student_skills
    }
    details = []
    contributions = []
    for required in required_skills:
        name = required["skill_name"]
        minimum = int(required.get("required_score", 0))
        current = score_by_name.get(name.strip().lower(), 0)
        contribution = 100 if minimum <= 0 else min(100, round((current / minimum) * 100))
        meets_requirement = current >= minimum
        details.append({
            "skill_name": name,
            "required_score": minimum,
            "current_score": current,
            "match_score": contribution,
            "status": "Strong match" if meets_requirement else "Needs improvement",
        })
        contributions.append(contribution)

    overall = round(sum(contributions) / len(contributions)) if contributions else 0
    return {
        "match_percentage": overall,
        "skill_matches": details,
    }