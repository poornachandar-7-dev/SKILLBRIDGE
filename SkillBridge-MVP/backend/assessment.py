# backend/assessment.py
#
# WHAT THIS FILE DOES:
# This module defines the Stage 4 Skill Assessment question bank,
# securely evaluates student answers on the server, and calculates
# standardized skill proficiency scores (0 - 100%).
#
# SECURITY RULES ENFORCED HERE:
#   - Correct answers are NEVER returned to the client in GET requests.
#   - Scoring is calculated strictly on the backend (never trust browser scores).
#   - Scores are normalized between 0 and 100 for consistent skill mapping.

from typing import List, Dict

# ---------------------------------------------------------
# QUESTION BANK (12 Questions: 3 per MVP Skill)
# ---------------------------------------------------------
# Each question contains:
#   - id: Unique integer identifier
#   - skill: The skill name (must match the name in the skills table)
#   - question: The question text displayed to the student
#   - options: 4 distinct choices
#   - correct_option: Index (0-3) of the correct choice (SERVER ONLY)
# ---------------------------------------------------------
ASSESSMENT_QUESTIONS = [
    # --- Python (Questions 1 - 3) ---
    {
        "id": 1,
        "skill": "Python",
        "question": "What is the correct file extension for Python source files?",
        "options": [".python", ".py", ".pyt", ".pt"],
        "correct_option": 1  # .py
    },
    {
        "id": 2,
        "skill": "Python",
        "question": "Which keyword is used to define a function in Python?",
        "options": ["function", "func", "def", "define"],
        "correct_option": 2  # def
    },
    {
        "id": 3,
        "skill": "Python",
        "question": "Which of the following data types is immutable in Python?",
        "options": ["list", "tuple", "dict", "set"],
        "correct_option": 1  # tuple
    },

    # --- Java (Questions 4 - 6) ---
    {
        "id": 4,
        "skill": "Java",
        "question": "Which keyword is used to declare a class in Java?",
        "options": ["class", "struct", "define", "object"],
        "correct_option": 0  # class
    },
    {
        "id": 5,
        "skill": "Java",
        "question": "What is the standard entry-point method signature for a Java application?",
        "options": [
            "public void start()",
            "public static void main(String[] args)",
            "void main()",
            "static int run()"
        ],
        "correct_option": 1  # public static void main(String[] args)
    },
    {
        "id": 6,
        "skill": "Java",
        "question": "Which primitive data type is used to store true or false values in Java?",
        "options": ["bool", "boolean", "bit", "int"],
        "correct_option": 1  # boolean
    },

    # --- Web Development (Questions 7 - 9) ---
    {
        "id": 7,
        "skill": "Web Development",
        "question": "Which HTML tag is used to create a clickable hyperlink?",
        "options": ["<link>", "<a>", "<href>", "<url>"],
        "correct_option": 1  # <a>
    },
    {
        "id": 8,
        "skill": "Web Development",
        "question": "Which CSS property is used to change the background color of an element?",
        "options": ["color", "background-color", "bgcolor", "canvas-color"],
        "correct_option": 1  # background-color
    },
    {
        "id": 9,
        "skill": "Web Development",
        "question": "Which JavaScript keyword is used to declare a variable that cannot be reassigned?",
        "options": ["var", "let", "const", "static"],
        "correct_option": 2  # const
    },

    # --- Data Structures (Questions 10 - 12) ---
    {
        "id": 10,
        "skill": "Data Structures",
        "question": "Which data structure operates on a First-In, First-Out (FIFO) basis?",
        "options": ["Stack", "Queue", "Tree", "Graph"],
        "correct_option": 1  # Queue
    },
    {
        "id": 11,
        "skill": "Data Structures",
        "question": "What is the average time complexity of accessing an element in an array by its index?",
        "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
        "correct_option": 0  # O(1)
    },
    {
        "id": 12,
        "skill": "Data Structures",
        "question": "Which data structure operates on a Last-In, First-Out (LIFO) basis?",
        "options": ["Queue", "Stack", "Linked List", "Binary Search Tree"],
        "correct_option": 1  # Stack
    }
]


def get_assessment_questions() -> List[Dict]:
    """
    Returns the list of assessment questions formatted for the frontend client.
    
    SECURITY CRITICAL:
    This function explicitly strips `correct_option` so students cannot inspect
    browser network requests to cheat on the assessment.
    """
    safe_questions = []
    for q in ASSESSMENT_QUESTIONS:
        safe_questions.append({
            "id": q["id"],
            "skill": q["skill"],
            "question": q["question"],
            "options": q["options"]
        })
    return safe_questions


def evaluate_assessment_answers(answers: Dict[int, int]) -> Dict[str, int]:
    """
    Evaluates submitted student answers against the question bank and calculates
    a proficiency score for each skill.
    
    Parameters:
        answers: Dictionary mapping question_id -> selected_option_index (0-3).
                 e.g. {1: 1, 2: 2, 3: 1, ...}
                 
    Returns:
        dict: Mapping skill_name -> score (0 to 100).
              e.g. {"Python": 100, "Java": 67, "Web Development": 100, "Data Structures": 67}
              
    SCORING FORMULA:
        For each skill:
            score = round((correct_answers_for_skill / total_questions_for_skill) * 100)
            
        Examples with 3 questions per skill:
            3 / 3 correct = 100%
            2 / 3 correct = 67%
            1 / 3 correct = 33%
            0 / 3 correct = 0%
            
        Guarantees score is an integer between 0 and 100.
    """
    # Count totals and correct answers per skill
    skill_totals: Dict[str, int] = {}
    skill_correct: Dict[str, int] = {}

    for q in ASSESSMENT_QUESTIONS:
        skill = q["skill"]
        qid = q["id"]
        correct_idx = q["correct_option"]

        skill_totals[skill] = skill_totals.get(skill, 0) + 1
        skill_correct.setdefault(skill, 0)

        # Check if the student answered this question correctly
        # Note: answers dictionary may have string or int keys
        selected_idx = answers.get(qid)
        if selected_idx is None:
            # Fallback check if keys were converted to strings in JSON
            selected_idx = answers.get(str(qid))

        if selected_idx is not None:
            try:
                if int(selected_idx) == correct_idx:
                    skill_correct[skill] += 1
            except (ValueError, TypeError):
                # Invalid option index treated as incorrect
                pass

    # Calculate percentage scores
    skill_scores: Dict[str, int] = {}
    for skill, total in skill_totals.items():
        correct = skill_correct.get(skill, 0)
        # Standard percentage rounded to nearest integer (0 to 100)
        percentage = round((correct / total) * 100)
        # Clamp strictly between 0 and 100
        clamped_score = max(0, min(100, percentage))
        skill_scores[skill] = clamped_score

    return skill_scores
