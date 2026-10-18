# CodeSense — Intelligent Compiler Error Analyzer & Educational Learning Platform

[![CI Pipeline](https://github.com/your-username/CodeSense/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/CodeSense/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6.svg?logo=typescript)](https://www.typescriptlang.org/)
[![OpenJDK](https://img.shields.io/badge/OpenJDK-17-ED8B00.svg?logo=openjdk)](https://openjdk.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)](https://www.docker.com/)

**CodeSense** is an intelligent educational Java compiler error analyzer and learning platform designed to bridge the gap between cryptic compiler diagnostics and student comprehension.

Instead of presenting beginners with raw, confusing compiler messages or relying on hallucinations from unstructured LLM prompts, CodeSense treats the **real Java compiler (`javac`) as the absolute source of truth**. It parses raw diagnostics into structured tokens, classifies errors into an educational taxonomy, generates root-cause breakdowns, and provides **compiler-verified automatic code fixes** that preserve the student's original code.

---

## Table of Contents

- [Core Product Philosophy](#core-product-philosophy)
- [Key Features](#key-features)
- [Architecture & Pipeline](#architecture--pipeline)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [Installation & Local Setup](#installation--local-setup)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [Docker Setup](#docker-setup)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [UI & Screenshots Walkthrough](#ui--screenshots-walkthrough)
- [Production Deployment](#production-deployment)
  - [Render Deployment](#render-deployment)
  - [Railway Deployment](#railway-deployment)
  - [Vercel & Netlify Deployment](#vercel--netlify-deployment)
- [Future Enhancements](#future-enhancements)
- [Contributors & Community](#contributors--community)
- [License](#license)

---

## Core Product Philosophy

1. **Compiler is the Source of Truth**: CodeSense never bypasses real compilation. Real compilation is executed via OpenJDK `javac` in isolated execution sandboxes.
2. **Deterministic Rules & Taxonomy First**: Compiler messages are parsed deterministically, line-by-line, and mapped into a structured pedagogical taxonomy (Syntax, Type, Variable, Method, Arithmetic, etc.).
3. **Compiler-Verified Code Corrections**: Automatic fixes are never generic or hallucinated. Proposed corrections preserve the user's actual program structure, modify only the necessary region, and **must successfully recompile cleanly (`javac exit 0`)** before being shown to the user.
4. **Graceful Zero-Dependency Fallback**: Operates completely offline out-of-the-box using the built-in Java Knowledge Base (`java_errors.json`) without requiring any paid AI API keys.
5. **Educational Empowerment**: Focuses on student learning with "What Happened", "Why it Happened", "How to Prevent it", and "Recommended Concept to Learn Next".

---

## Key Features

- **Monaco Code Editor**: Professional Java syntax highlighting, gutter error glyphs, inline squiggly markers, and line highlighting.
- **Compiler Error Parser**: Extracts exact file, line, column, severity, compiler error code, and problematic snippets from `javac` output.
- **Deterministic Fix Engine**: Generates targeted candidate corrections for type mismatches, missing semicolons, variable typos, division by zero, checked exceptions, and diamond operator mismatches.
- **Recompilation Verification**: Every proposed fix is re-tested against `javac`. Unsafe or ambiguous errors (e.g. unknown methods or missing interface implementations) are safely marked as `fix_available: false` with clear guidance instead of fabricating code.
- **One-Click "Apply Fix"**: Instantly replaces the code in the Monaco Editor with the compiler-validated correction.
- **Static Analysis Heuristics**: Detects pre-compilation code smells including unused variables, empty catch blocks, accidental infinite loops, and `==` string equality bugs.
- **Submission History**: Detailed timeline tracking past submissions, compilation times, error categories, and historical inspection.
- **Personalized Insights Dashboard**: Visual breakdown of error taxonomy distribution, most frequent mistakes, and curated study recommendations.

---

## Architecture & Pipeline

```
User Java Code
      ↓
OpenJDK javac Compiler
      ↓
Raw Compiler Output (stderr / stdout)
      ↓
JavaErrorParser (regex tokenizer & token extractor)
      ↓
ErrorClassifier Engine (deterministic taxonomy categorizer)
      ↓
SourceContextExtractor (declared variables, methods, scope context)
      ↓
JavaFixEngine (candidate generation & multi-error loop)
      ↓
javac Recompilation Validation Loop
      ↓
Validated Corrected Source Code (or safe fallback notice)
      ↓
FastAPI Backend (REST Endpoints)
      ↓
React + TypeScript Frontend (Monaco Editor + Educational Diagnostics)
```

---

## Technology Stack

| Layer | Technologies |
| --- | --- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Monaco Editor (`@monaco-editor/react`), Lucide React, Axios |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn, pytest, httpx |
| **Compiler** | OpenJDK 17 `javac` |
| **Database** | PostgreSQL (Docker/Production) / SQLite (Zero-configuration Local Development) |
| **AI Layer** | `AIExplanationService` with Google Gemini / OpenAI format + Deterministic Knowledge Base Fallback |
| **DevOps & CI** | Docker, Docker Compose, Nginx, GitHub Actions |

---

## Folder Structure

```
CodeSense/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── workflows/
│   │   └── ci.yml                 # Automated testing and build pipeline
│   └── pull_request_template.md
├── backend/
│   ├── app/
│   │   ├── ai/                    # AIExplanationService & prompts
│   │   ├── analyzers/             # JavaStaticAnalyzer heuristics
│   │   ├── api/                   # FastAPI routes (/analyze, /history, /insights, /health)
│   │   ├── classifiers/           # ErrorClassifier taxonomy engine
│   │   ├── compiler/              # JavaCompilerService, JavaErrorParser, JavaFixEngine
│   │   ├── database/              # SQLAlchemy engine, models, session
│   │   ├── knowledge/             # ErrorKnowledgeBase & java_errors.json
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── utils/                 # Logging and helper utilities
│   │   ├── config.py              # Application settings
│   │   └── main.py                # FastAPI entrypoint
│   ├── tests/                     # 43 automated regression tests
│   ├── .env.example
│   ├── Dockerfile
│   ├── Procfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # MonacoEditor, ErrorCard, AnalysisPanel, Navbar
│   │   ├── pages/                 # AnalyzerPage, HistoryPage, InsightsPage
│   │   ├── services/              # Axios API client (api.ts)
│   │   ├── types/                 # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── .env.example
│   ├── Dockerfile
│   ├── nginx.conf                 # Production Nginx reverse proxy configuration
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vercel.json
│   ├── netlify.toml
│   └── vite.config.ts
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── LICENSE                        # MIT License
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── render.yaml                    # Render deployment blueprint
├── railway.toml                   # Railway deployment config
└── README.md
```

---

## Installation & Local Setup

### Prerequisites

- **Git**
- **Python 3.12+**
- **Node.js 20+** and `npm`
- **OpenJDK 17+** (Ensure `javac -version` works in your terminal)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated test suite
python -m pytest

# Start development backend on port 8001
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Backend will be available at:
- **API Root**: `http://127.0.0.1:8001`
- **Swagger UI Docs**: `http://127.0.0.1:8001/docs` or `http://127.0.0.1:8001/api/docs`
- **Health Check**: `http://127.0.0.1:8001/api/health`

### 2. Frontend Setup

```bash
# In a separate terminal, navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server on port 5173
npm run dev
```

Frontend will be available at `http://localhost:5173`.

---

## Docker Setup

Run the entire full-stack application (PostgreSQL + FastAPI Backend with OpenJDK + Nginx Frontend) with a single command:

```bash
# Clone the repository
git clone https://github.com/your-username/CodeSense.git
cd CodeSense

# Copy environment example
cp .env.example .env

# Build and start all services
docker compose up --build
```

- **Frontend App**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

To stop the containers:
```bash
docker compose down
```

---

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Deployment environment (`production` or `development`) |
| `DATABASE_URL` | `sqlite:///./codesense.db` | PostgreSQL or SQLite database connection string |
| `API_KEY` / `AI_API_KEY` | *(Optional)* | Google Gemini or OpenAI API key (KB used if empty) |
| `AI_MODEL` | `gemini-2.5-flash` | Target model for AI explanation generation |
| `BACKEND_HOST` | `0.0.0.0` | Host binding address |
| `BACKEND_PORT` | `8000` | Port for the backend service |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origin for frontend |
| `JAVA_COMPILER_PATH` | `javac` | Path to the OpenJDK compiler binary |
| `COMPILATION_TIMEOUT_SECONDS` | `10` | Hard timeout limit for compilation processes |
| `VITE_API_URL` | `http://127.0.0.1:8001` | Backend URL consumed by the React client |

---

## API Documentation

CodeSense provides automatic OpenAPI (Swagger) documentation available at `/docs` or `/api/docs`.

### Core Endpoints

| Method | Path | Summary | Description |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Health Check | Validates OpenJDK compiler status, version, and database readiness |
| `POST` | `/api/analyze` | Full Code Analysis | Compiles Java code, classifies errors, runs static heuristics, generates validated fixes |
| `POST` | `/api/compile` | Raw Compilation | Runs raw javac compiler without generating educational explanations |
| `POST` | `/api/explain` | Explain Error | Generates educational explanation and fix for a single diagnostic token |
| `GET` | `/api/history` | Submission History | Returns paginated historical submissions and compilation results |
| `GET` | `/api/history/{id}` | Submission Detail | Returns full retrospective diagnostic records for a specific submission |
| `GET` | `/api/insights` | Learning Insights | Returns error taxonomy distribution, frequency trends, and recommendations |

### Example Request (`POST /api/analyze`)

```json
{
  "language": "java",
  "source_code": "public class Main {\n    public static void main(String[] args) {\n        int age = \"twenty\";\n        System.out.println(age);\n    }\n}",
  "user_id": "student-1"
}
```

### Example Response (`200 OK`)

```json
{
  "submission_id": "8dc1a03f-45e6-42bc-9d21-f92cb71a3962",
  "language": "java",
  "success": false,
  "exit_code": 1,
  "compilation_time_ms": 420.5,
  "raw_output": "Main.java:3: error: incompatible types: String cannot be converted to int...",
  "errors": [
    {
      "error": {
        "line": 3,
        "column": 19,
        "severity": "error",
        "message": "incompatible types: String cannot be converted to int",
        "compiler_code": "INCOMPATIBLE_TYPES"
      },
      "classification": {
        "category": "TYPE_ERROR",
        "subcategory": "INCOMPATIBLE_TYPES",
        "confidence": 0.98
      },
      "explanation": {
        "title": "Type Mismatch",
        "what_happened": "You attempted to assign text to an integer variable.",
        "why_it_happened": "Java requires variable types to match the assigned expression.",
        "fix_available": true,
        "corrected_code": "public class Main {\n    public static void main(String[] args) {\n        int age = 20;\n        System.out.println(age);\n    }\n}",
        "changed_lines": [3],
        "validated": true
      }
    }
  ],
  "warnings": [],
  "primary_error": null,
  "summary_message": "Compilation failed with 1 compiler error."
}
```

---

## UI & Screenshots Walkthrough

```
+-----------------------------------------------------------------------------------+
|  CodeSense   [Analyzer]  [History]  [Insights]                     [Status: Ready] |
+-----------------------------------------------------------------------------------+
|  PRESETS: [Type Mismatch] [Missing Semicolon] [Typo] [Div by Zero]                |
+------------------------------------------+----------------------------------------+
|  JAVA CODE EDITOR (Monaco)               |  ANALYSIS & DIAGNOSTICS                |
|  1  public class Main {                  |  [Errors (1)]  [Detailed Explanation]  |
|  2      public static void main(...) {   |  ------------------------------------  |
|  3  >>>     int age = "twenty";  [x]     |  ERROR #1  TYPE_ERROR  Line 3:19       |
|  4          System.out.println(age);     |  Compiler Message:                     |
|  5      }                                |  incompatible types: String -> int     |
|  6  }                                    |                                        |
|                                          |  Suggested Fix:                        |
|                                          |  Change string literal to int literal. |
|                                          |                                        |
|  [ Analyze Code ]  [ Quick Compile ]     |  [Compiler Verified] [ Apply Fix ]     |
|                                          |  Corrected Code:                       |
|                                          |  int age = 20;                         |
+------------------------------------------+----------------------------------------+
```

### Key UI Features
1. **Interactive Preset Dropdown**: Instantly load typical compiler error scenarios (syntax, type mismatch, undefined method, division by zero).
2. **Synchronized Editor Glyphs**: Red gutter markers and inline squigglies jump directly to problematic lines.
3. **Validated Code Preview**: Verified fixes feature a "Compiler Verified" badge and one-click "Apply Fix".
4. **Learning Insights Page**: Color-coded bar charts visualizing your error profile over time.

---

## Production Deployment

### Deployment Architecture

```
GitHub
  ↓
CodeSense repository
  │
  ├── frontend
  │      ↓
  │    Vercel
  │      ↓
  │   codesense.vercel.app
  │
  └── backend
         ↓
       Render
         ↓
   codesense-api.onrender.com
         ↓
      OpenJDK
         ↓
       javac
```

### 1. Backend Deployment (Render)

The backend runs as a Docker Web Service on **Render** so it can execute real Java compilation via **OpenJDK 17 (`javac`)**:

1. Log in to [Render](https://render.com) and click **New +** > **Web Service**.
2. Connect your GitHub repository (`CodeSense`).
3. Configure the service settings:
   - **Name**: `codesense-api` *(renders as `codesense-api.onrender.com`)*
   - **Root Directory**: `backend` (or leave root and select Dockerfile path `./backend/Dockerfile`)
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./backend/Dockerfile`
   - **Docker Context**: `./backend`
   - **Instance Type**: Free
4. Add the following **Environment Variables**:
   | Key | Value | Notes |
   | --- | --- | --- |
   | `ENVIRONMENT` | `production` | Enables production mode |
   | `FRONTEND_URL` | `https://codesense.vercel.app` | Configures CORS for Vercel |
   | `DATABASE_URL` | `sqlite:///./codesense.db` | Local SQLite file storage |
   | `AI_API_KEY` | *(Optional)* | Gemini API Key for AI explanations (offline KB fallback active by default) |
   | `AI_MODEL` | `gemini-2.5-flash` | Default Gemini model |
   | `COMPILATION_TIMEOUT_SECONDS` | `10` | Compilation sandbox timeout |
5. Click **Create Web Service**.
6. Verify deployment by visiting `https://codesense-api.onrender.com/api/health`. You should receive:
   ```json
   {
     "status": "healthy",
     "app": "CodeSense",
     "compiler": {
       "available": true,
       "version": "javac 17.0.x"
     }
   }
   ```

*(Alternatively, select **Blueprints** and connect `render.yaml` for automatic one-click setup.)*

---

### 2. Frontend Deployment (Vercel)

The frontend is a React + Vite Single-Page Application (SPA) deployed on **Vercel**:

1. Log in to [Vercel](https://vercel.com) and click **Add New...** > **Project**.
2. Import your GitHub repository (`CodeSense`).
3. In the configuration modal:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click edit and choose `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Expand **Environment Variables** and add:
   | Key | Value |
   | --- | --- |
   | `VITE_API_URL` | `https://codesense-api.onrender.com` |
5. Click **Deploy**.
6. Set custom domain (optional) or use `codesense.vercel.app`.
7. SPA client-side routing and cache control are automatically handled by [`frontend/vercel.json`](frontend/vercel.json).

---

### Alternative: Railway Deployment

The repository also contains `railway.toml` and `backend/Procfile`.
1. In [Railway](https://railway.app), click **New Project** > **Deploy from GitHub repo**.
2. Railway detects `backend/Dockerfile` and spins up the backend with OpenJDK and health checks.

---

## Future Enhancements

- [ ] **Multi-File Java Projects**: Support compilation of multi-class and package structures.
- [ ] **Interactive Code Stepping**: Step-by-step visualizer for variable values and call stacks.
- [ ] **Additional Languages**: Extend the compiler-truth architecture to C++ (`clang++`) and Rust (`rustc`).
- [ ] **LTI Canvas / Blackboard Integration**: Embed CodeSense assignments into university LMS portals.
- [ ] **Interactive Quiz Mode**: Test student understanding of compiler errors before showing solutions.

---

## Contributors & Community

Contributions, feature requests, and feedback are warmly welcomed!

- **Issues**: [GitHub Issues](https://github.com/your-username/CodeSense/issues)
- **Guidelines**: Review [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.
- **Code of Conduct**: Review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## License

CodeSense is open-source software licensed under the [MIT License](LICENSE).