# SkillBridge
### Academia–Industry Skill Collaboration & Employability Platform
**Assess skills. Identify gaps. Improve. Connect with opportunities.**

🔗 **Live Demo:** [skill-bridge-mvp--puthijoshith.replit.app](https://skill-bridge-mvp--puthijoshith.replit.app/)

---

## 📌 Overview

**SkillBridge** is a skill-centered platform that connects students, industry, and academic institutions in a unified collaborative ecosystem. Instead of relying solely on conventional resumes and static job listings, SkillBridge emphasizes actual technical abilities, actionable skill gap analysis, verified company screening tests, and continuous professional improvement.

- **Students:** Assess capability, discover missing skills, complete company screening tests, earn XP/badges, and find matched internships.
- **Industry:** Define required technical skills, configure custom evaluation screening tests, and hire candidates based on verified signal.
- **Institutions:** Gain aggregate visibility into cohort readiness, identify common curriculum skill gaps, and align training programs with industry demand.

---

## 🚨 Problem Statement

| Stakeholder | Challenges Faced |
| :--- | :--- |
| **Students** | Don't know their actual skill readiness or market expectations; struggle to find opportunities matched to their real technical ability. |
| **Industry** | Overwhelmed with resume volume that rarely reflects hands-on coding proficiency; hard to screen candidates on specific stack requirements. |
| **Institutions** | Limited visibility into aggregate student capability and common skill gaps; curriculum updates lag behind changing industry standards. |

---

## 💡 Our Solution: The Skill-First Ecosystem

SkillBridge delivers a continuous skill-first journey:

```text
Assessment ➔ Skill Profile ➔ Skill Gap Analysis ➔ Targeted Improvement ➔ Opportunity Matching ➔ Company Screening ➔ Application ➔ Progress Tracking & Badges
```

### What Makes SkillBridge Different?

| Conventional Job Portal | SkillBridge Platform |
| :--- | :--- |
| Static job listings | Verified, skill-based opportunity matching |
| Resume-focused screening | Demonstrated skills + baseline assessment + company screening tests |
| Passive student job search | Algorithmic matching connects students to best-fit opportunities |
| Little to no candidate feedback | Instant skill gap diagnosis shows exactly what to improve |
| Disconnected student ↔ recruiter relationship | Tri-party collaboration: Student ↔ Industry ↔ Institution |
| Transactional placement focus | Continuous skill development, streaks, and milestone achievements |

---

## 👥 User Roles & 3-Step Onboarding

### 1. Student
- **Demographics on Signup:** Full Name, Age (14–100), Gender (`Male`, `Female`, `Other`, `Prefer not to say`), Email & bcrypt-hashed Password.
- **Features:**
  - Take foundational assessments in Python, Java, Web Development, and Data Structures.
  - View readiness score ring and personalized skill gap breakdown.
  - Discover and apply to matched internships with percentage compatibility scores.
  - Take company-specific screening tests and view immediate score feedback.
  - Earn XP (+50 XP per passed test), maintain streaks, and unlock milestone badges (e.g., `Screening Star`).

### 2. Industry / Employer
- Register company profile and post internship/job opportunities.
- Specify required technical domains and minimum proficiency thresholds.
- **Company Screening Test Builder:** Build custom multiple-choice screening tests with passing thresholds, time limits, and explanation notes.
- **Candidate Evaluation Desk:** Review applicants with demographic signals (Age, Gender), technical skill match %, and screening test status (*Passed*, *Failed*, or *Pending*).
- Shortlist or reject candidates with one click.

### 3. Institution / Academician
- View aggregate cohort readiness and assessment coverage percentages.
- Benchmark cohort performance across all technical skill domains.
- Identify common skill gaps across student cohorts to design targeted workshops and curriculum enhancements.
- Respects student privacy: individual student scores remain confidential while institutions receive cohort-level intelligence.

---

## 🔐 Authentication & Onboarding Flow

A role-aware signup and login system:

1. **3-Step Registration Wizard:**
   - **Step 1 — Account Setup:** Email, Password with real-time dynamic strength meter (color-coded *Weak* / *Fair* / *Good* / *Strong* bar with criteria checklist for length, uppercase, lowercase, numbers/symbols), and Confirm Password match indicator.
   - **Step 2 — Personal Details:** Full Name, Age (numeric validation 14–100), and Gender pill selectors (`Male`, `Female`, `Other`, `Prefer not to say`).
   - **Step 3 — Role Selection:** Interactive selection cards for **Student**, **Industry**, **Academician**, or **Institution**, with registration summary confirmation before submission.
2. **Password Security:** Passwords hashed with bcrypt before SQLite storage; plaintext passwords are never stored.
3. **Session Handling:** Issues JSON Web Tokens (JWT) on login/registration attached via `Authorization: Bearer <token>`.
4. **Frictionless Handoff:** New signups are automatically authenticated and redirected to their role-specific dashboard.
5. **Protected Routes:** Role-based access control (RBAC) middleware protects all backend API endpoints.

---

## ⭐ Core Features

| Feature | Description |
| :--- | :--- |
| **Skill Assessment** | Evaluates ability across Python, Java, Web Dev, and Data Structures with randomized questions. |
| **Skill Profile** | Consolidated visual readiness ring and individual proficiency ratings (0–100%). |
| **Skill Gap Analysis** | Compares student capabilities against opportunity requirements, flagging priority improvement areas. |
| **Opportunity Management** | Industry recruiters post roles with target skills, descriptions, and required scores. |
| **Skill-Based Matching** | Automatically computes candidate match scores and recommends top-fitting opportunities. |
| **Applications Desk** | Track application status (*applied*, *shortlisted*, *accepted*, *rejected*) in real-time. |
| **Company Screening Tests** | Custom multi-choice screening tests created by employers for opportunities with pass criteria. |
| **Screening Test Runner** | Interactive modal test runner for students with automatic grading and hidden answer keys. |
| **XP & Streak System** | Rewards meaningful engagement (+50 XP for screening tests, daily check-in streaks). |
| **Milestone Badges** | Unlocks achievement badges such as **Screening Star**, **First Step**, **Python Pro**, and **Algo Ace**. |
| **Leaderboard** | Cohort ranking based on XP, level progression, and assessment readiness. |
| **Institution Analytics** | Cohort skill distribution, common gaps, and curriculum alignment metrics. |

---

## 🏗️ System Architecture

```text
 Client Layer (Modern React 19 + Vite SPA, Tailwind CSS, Lucide Icons, Legacy HTML Templates)
                                        │
                                        ▼ HTTPS / REST
 API Gateway & Security Layer (FastAPI Router, JWT Bearer Auth, bcrypt Hashing, RBAC Middleware)
                                        │
                                        ▼ Authorized Calls
 Application Service Layer:
   ├── Assessment Engine & Auto-Scoring
   ├── Skill Gap & Matching Algorithm
   ├── Company Screening Test Service
   ├── Opportunity & Application Management
   ├── Gamification Engine (XP, Streaks, Badges)
   └── Institution Cohort Analytics
                                        │
                                        ▼ SQL
 Data Layer (SQLite Database: users, skills, student_skills, opportunities, applications,
              screening_tests, screening_questions, screening_attempts, student_gamification)
```

---

## 🛠️ Technology Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Wouter, TanStack React Query, Lucide Icons.
- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
- **Database:** SQLite 3 with Foreign Keys & Indexes enabled.
- **Security:** JWT (`PyJWT`), Password Hashing (`bcrypt`), Role-Based Access Control (RBAC).

---

## 📁 Repository Structure

```text
SkillBridge-MVP/
├── backend/                        # Python FastAPI application (core backend)
│   ├── __init__.py                 # Python package initialization
│   ├── assessment.py               # Foundational assessment questions & scoring logic
│   ├── auth.py                     # User authentication, bcrypt hashing & JWT tokens
│   ├── database.py                 # SQLite database schema, CRUD, screening & badges
│   ├── main.py                     # FastAPI server, REST API endpoints & static SPA router
│   ├── matching.py                 # Skill gap calculation & matching algorithm
│   └── test_e2e_features.py        # End-to-end automated integration test suite
│
├── frontend/                       # Dedicated frontend application & templates
│   ├── public/                     # Static assets (favicon, robots.txt)
│   ├── src/                        # Modern React Single Page Application
│   │   ├── components/             # Reusable UI components & dialogs
│   │   ├── hooks/                  # Custom React hooks (toast, mobile)
│   │   ├── lib/                    # Utility helpers
│   │   ├── pages/                  # Page views
│   │   ├── App.tsx                 # Core App router, multi-step signup & screening modals
│   │   ├── index.css               # Design tokens, variables & animations
│   │   └── main.tsx                # React root entry
│   ├── legacy/                     # Standalone prototype HTML templates (3-step wizard, dashboards)
│   │   ├── home.html, roles.html, login.html, register.html
│   │   ├── student_dashboard.html, assessment.html, leaderboard.html
│   │   └── industry_dashboard.html, institution_dashboard.html
│   ├── dist/public/                # Production build artifacts served by FastAPI
│   ├── package.json, vite.config.ts, tsconfig.json
│
├── data/                           # Local SQLite database storage
│   └── skillbridge.db              # SQLite database file
│
├── lib/                            # Shared workspace packages
│   ├── api-client-react/           # React Query API client & types
│   ├── api-spec/                   # OpenAPI 3.0 specification
│   ├── api-zod/                    # Zod validation schemas
│   └── db/                         # Drizzle schema definitions
│
├── start.bat                       # Windows 1-click launcher script
├── run.bat                         # Shortcut alias for start.bat
├── requirements.txt                # Python dependencies
├── package.json                    # Workspace monorepo manifest
├── pnpm-workspace.yaml             # PNPM workspace configuration
└── README.md                       # Platform documentation (this file)
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+** installed and available in your `PATH`.
- **Node.js 18+** & **pnpm** (or npm).

### 1. Fast Start (Windows)
Double-click `start.bat` or run:
```powershell
.\start.bat
```
This script automatically:
1. Verifies/creates the Python virtual environment.
2. Installs required Python dependencies.
3. Initializes the SQLite database schema and seed data.
4. Builds the frontend if needed.
5. Starts the FastAPI server and launches your browser at `http://127.0.0.1:8000`.

### 2. Manual Setup

#### Backend Setup:
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt

# Run FastAPI server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend Setup (Development):
```bash
# Navigate to frontend
cd frontend

# Install dependencies
pnpm install

# Run Vite dev server
pnpm run dev
```

#### Build Production Bundle:
```bash
pnpm --filter @workspace/skillbridge-app run build
```

---

## 🧪 Running Automated Tests

Run the comprehensive end-to-end integration test suite:
```bash
python backend/test_e2e_features.py
```
This validates:
- [x] Registration with demographic fields (`age`, `gender`).
- [x] JWT login and sanitized student profile retrieval.
- [x] Industry opportunity creation with skill requirements.
- [x] Recruiter screening test configuration (verifies answer keys are hidden from candidates).
- [x] Student application submission & interactive screening test evaluation.
- [x] Automatic scoring, +50 XP award, and unlocking the `screening_star` badge.
- [x] Recruiter candidate evaluation displaying applicant demographics and screening status.

---

## 🔗 Key API Endpoints

### Authentication
- `POST /api/auth/register` — Multi-step registration (name, email, password, role, age, gender).
- `POST /api/auth/login` — Authenticate and obtain JWT access token.
- `GET /api/auth/me` — Retrieve current authenticated user session.

### Opportunities & Applications
- `GET /api/opportunities` — List opportunities with skill requirements and student match %.
- `POST /api/opportunities` — Post a new internship (Industry only).
- `POST /api/opportunities/{id}/apply` — Apply to an opportunity (Student only).
- `GET /api/student/applications` — List student's applications with screening test status.
- `GET /api/industry/opportunities/{id}/applicants` — List applicants with demographics and screening scores.
- `PATCH /api/applications/{id}/status` — Update application status (*shortlisted*, *rejected*, *accepted*).

### Company Screening Tests
- `POST /api/opportunities/{id}/screening-test` — Configure or edit screening test (Industry only).
- `GET /api/opportunities/{id}/screening-test` — Get screening test (answers stripped for candidates).
- `GET /api/screening-tests/{id}` — Get screening test details and question set.
- `POST /api/screening-tests/{id}/submit` — Submit answers, auto-grade, earn XP, and unlock badges.
- `GET /api/screening-tests/{id}/my-attempt` — Get student's attempt record.

### Student & Institution
- `GET /api/student/profile` — Student profile, skills, readiness score, and gamification state.
- `GET /api/student/skill-gaps` — Gap analysis comparing student abilities with target roles.
- `GET /api/institution/stats` — Aggregate student readiness and common skill gaps (Institution only).

---

## 📊 Example Use Case

A student applies for a **Backend Python Developer** internship requiring Python, SQL, and System Architecture:
1. **Skill Assessment:** Student scores 85% in Python and 55% in Data Structures.
2. **Gap Analysis:** SkillBridge identifies System Architecture and advanced algorithms as priority gaps.
3. **Screening Test:** The employer requires a 3-question screening test (70% passing threshold).
4. **Completion:** The student takes the test, scores 100%, earns **+50 XP**, and unlocks the **Screening Star** badge.
5. **Recruiter Evaluation:** The employer's desk shows the applicant as `Age: 22y · Female · Match: 88% · Screening: 100% (Passed)` and shortlists the candidate.
6. **Institutional Insight:** The academic department sees that 45% of students in the cohort scored low in System Architecture, prompting a targeted faculty workshop.

---

## 🔮 Future Scope

- **AI-Powered Assessments:** Dynamically generated technical interview questions tailored to specific job postings.
- **Mock Interview Simulator:** Chat-based interactive interview simulator providing live code and behavioral feedback.
- **Verified Portfolio Evidence:** Upload and verify GitHub repositories, live demo URLs, and project artifacts.
- **Peer Skill Benchmarking:** Cohort comparison charts visualizing individual percentiles against peer distributions.
- **Curriculum Recommendation Engine:** Automated academic syllabus recommendations based on hiring trends.

---

## 📄 License & Team

Built with ❤️ for academia–industry collaboration and employability enablement.
