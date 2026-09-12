# SkillBridge MVP — File Structure

This document provides a complete breakdown of the project directories and files in **SkillBridge-MVP**.

---

## 1. Directory Tree Overview

```text
SkillBridge-MVP/
├── backend/                      # Python FastAPI application (core backend)
│   ├── __init__.py               # Python package initialization
│   ├── assessment.py             # Assessment questions & answer evaluation logic
│   ├── auth.py                   # User authentication, bcrypt hashing & JWT tokens
│   ├── database.py               # SQLite database setup, queries, and CRUD operations
│   ├── main.py                   # Main FastAPI server, REST API routes & HTML UI
│   └── matching.py               # Skill gap calculation & matching algorithm
│
├── frontend/                     # Dedicated frontend application & templates
│   ├── public/                   # Static assets (favicon, robots.txt)
│   ├── src/                      # React source code (modern SPA)
│   │   ├── components/           # Reusable UI components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── lib/                  # Frontend utility libraries
│   │   ├── pages/                # Route page components
│   │   ├── App.tsx               # Main application root component & routing
│   │   ├── index.css             # Global styles & Tailwind directives
│   │   └── main.tsx              # Frontend entry point
│   ├── legacy/                   # Standalone prototype HTML templates
│   │   ├── assessment.html       # Assessment evaluation page
│   │   ├── home.html             # Landing page
│   │   ├── industry_dashboard.html # Industry recruiter dashboard
│   │   ├── institution_dashboard.html # Institution analytics dashboard
│   │   ├── leaderboard.html      # Cohort leaderboard page
│   │   ├── login.html            # User login page
│   │   ├── register.html         # User registration page
│   │   ├── roles.html            # Role selector page
│   │   └── student_dashboard.html # Student profile & gamification dashboard
│   ├── components.json           # UI component registry configuration
│   ├── index.html                # Single-page application HTML entry
│   ├── package.json              # Frontend dependencies & npm scripts
│   ├── tsconfig.json             # TypeScript configuration for frontend
│   └── vite.config.ts            # Vite development & build configuration
│
├── data/                         # Local data storage
│   └── skillbridge.db            # SQLite database file
│
├── artifacts/                    # Additional monorepo services and modules
│   ├── api-server/               # Node.js API server wrapper / runner
│   │   ├── build.mjs             # Esbuild bundling script
│   │   ├── package.json          # API server package manifest & dev scripts
│   │   └── tsconfig.json         # TypeScript configuration
│   │
│   └── mockup-sandbox/           # UI mockup sandbox & prototype workspace
│       ├── index.html            # Sandbox HTML entry
│       ├── package.json          # Sandbox package dependencies
│       └── vite.config.ts        # Sandbox Vite configuration
│
├── lib/                          # Shared workspace libraries (TypeScript monorepo)
│   ├── api-spec/                 # API contract & OpenAPI definition
│   │   ├── openapi.yaml          # OpenAPI 3.0 specification file
│   │   └── package.json          # Codegen scripts for client & schemas
│   │
│   ├── api-client-react/         # Auto-generated React Query API client
│   │   ├── src/                  # Generated React hooks and API client methods
│   │   ├── package.json          # Package manifest
│   │   └── tsconfig.json         # TypeScript compiler configuration
│   │
│   ├── api-zod/                  # Auto-generated Zod validation schemas & types
│   │   ├── src/                  # Generated Zod schemas & TypeScript models
│   │   ├── package.json          # Package manifest
│   │   └── tsconfig.json         # TypeScript compiler configuration
│   │
│   └── db/                       # Database schema & migrations (Drizzle ORM)
│       ├── src/                  # Drizzle ORM schema definitions
│       ├── drizzle.config.ts     # Drizzle configuration
│       ├── package.json          # Database package manifest
│       └── tsconfig.json         # TypeScript compiler configuration
│
├── scripts/                      # Workspace maintenance & automation scripts
│   ├── src/                      # Script sources
│   │   └── hello.ts              # Sample script
│   ├── post-merge.sh             # Git post-merge lifecycle hook
│   ├── package.json              # Scripts package manifest
│   └── tsconfig.json         # TypeScript compiler configuration
│
├── start.bat                     # Windows batch launcher (starts FastAPI server & opens browser)
├── run.bat                       # Shortcut alias for start.bat
├── requirements.txt              # Python dependencies (FastAPI, Uvicorn, bcrypt, PyJWT, etc.)
├── package.json                  # Root monorepo workspace manifest
├── pnpm-workspace.yaml           # PNPM workspace configuration
├── pnpm-lock.yaml                # Monorepo locked package dependency tree
├── tsconfig.base.json            # Shared base TypeScript compiler options
├── tsconfig.json                 # Monorepo project references configuration
├── .env.example                  # Template for environment configuration variables
├── .gitignore                    # Git file exclusions
├── .npmrc                        # NPM / PNPM package manager configuration
├── .replit                       # Replit cloud container and workflow setup
├── .replitignore                 # Replit build file exclusions
└── replit.md                     # System overview and operational guide
```

---

## 2. Directory Breakdown & Responsibilities

### `backend/`
Contains the Python-based backend application powered by FastAPI and SQLite.
- **`main.py`**: The primary entry point of the backend. Configures FastAPI, defines REST endpoints (health, skills, auth, opportunities, assessments), serves the modern React SPA web application from `frontend/dist/public`, and maintains legacy prototype views under `/legacy/*`.
- **`database.py`**: Handles SQLite database connections, table creation (`init_db`), seed data, and data access functions for users, skills, assessments, and opportunities.
- **`auth.py`**: Implements authentication security, including password hashing with bcrypt, JWT token generation, and dependency injection for authenticated routes.
- **`assessment.py`**: Stores questions and provides scoring logic for student skill evaluations.
- **`matching.py`**: Computes skill gaps and calculates compatibility scores between students and opportunities.

### `frontend/`
Dedicated frontend directory containing both the modern React single-page application and legacy prototype views.
- **Modern React App (`src/`, `public/`, `dist/`)**: Built with Vite, React 19, TypeScript, Tailwind CSS, Lucide icons, and TanStack React Query.
- **Legacy Templates (`legacy/`)**: Standalone HTML templates for quick prototype views served directly by FastAPI under `/legacy/*`.

### `data/`
Dedicated local storage for file-based persistence.
- **`skillbridge.db`**: The SQLite database file created and updated automatically by `backend/database.py`.

### `artifacts/`
Contains additional auxiliary services and prototypes within the monorepo workspace.
- **`api-server/`**: A Node.js / Express workspace service layer used for bundling or proxying backend services.
- **`mockup-sandbox/`**: An isolated playground environment for rapid UI design and mockup testing.

### `lib/`
Shared TypeScript libraries utilized across the monorepo workspace.
- **`api-spec/`**: Contains the OpenAPI (`openapi.yaml`) definition which acts as the contract for the API.
- **`api-client-react/`**: React Query client automatically generated from the OpenAPI spec for seamless frontend data fetching.
- **`api-zod/`**: Zod validation schemas and TypeScript type definitions generated from the OpenAPI spec.
- **`db/`**: Drizzle ORM schema definitions and database migration configuration for PostgreSQL/relational schemas.

### `scripts/`
Contains repository automation and maintenance utilities.
- **`post-merge.sh`**: Hook script executed after merging branches to sync dependencies.
- **`src/`**: TypeScript utility scripts run via `pnpm`.

---

## 3. Root Configuration & Scripts

| File | Type | Purpose |
| :--- | :--- | :--- |
| **`start.bat`** | Windows Batch | Launches the local FastAPI backend server with hot-reload, validates Python and dependencies, and opens `http://localhost:8000` in the browser. |
| **`run.bat`** | Windows Batch | Convenient shortcut alias that invokes `start.bat`. |
| **`requirements.txt`** | Config | Lists required Python packages (`fastapi`, `uvicorn`, `bcrypt`, `PyJWT`, `pydantic`, `python-dotenv`). |
| **`package.json`** | Config | Monorepo root package file with scripts for typechecking and building. |
| **`pnpm-workspace.yaml`** | Config | Defines the PNPM workspace packages under `artifacts/*`, `lib/*`, and `scripts`. |
| **`pnpm-lock.yaml`** | Lockfile | Locks dependency versions across all TypeScript/JavaScript packages. |
| **`tsconfig.base.json`** | Config | Centralized TypeScript compiler options extended by subpackages. |
| **`tsconfig.json`** | Config | Root TypeScript solution configuration linking workspace projects. |
| **`.env.example`** | Config | Example environment configuration file with default variables. |
| **`.gitignore`** | Config | Specifies files and patterns to exclude from version control. |
| **`.npmrc`** | Config | Configures package manager installation and resolution policies. |
| **`.replit`** | Config | Defines container configuration, modules, and workflows for Replit. |
| **`replit.md`** | Markdown | High-level workspace documentation and run instructions. |
