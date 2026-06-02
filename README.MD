# CrewAI Content Production System

> An autonomous AI content agency powered by CrewAI — multiple AI agents collaborating to research, write, edit, and optimize content end-to-end.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Team](#team)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [What's Built (Phase 1)](#whats-built-phase-1)
- [API Reference](#api-reference)
- [Extended Features & APIs](#extended-features--apis)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [Development Workflow](#development-workflow)
- [TODO / Remaining Work](#todo--remaining-work)
- [Roadmap](#roadmap)

---

## Project Overview

This platform simulates a real-world AI content agency where multiple specialized AI agents collaborate to produce high-quality content autonomously.

**Full pipeline (target):**

```
User Content Brief
        ↓
Researcher Agent       → searches web, gathers facts
        ↓
Writer Agent           → drafts the article
        ↓
Editor Agent           → refines tone and clarity
        ↓
SEO Optimizer Agent    → improves discoverability
        ↓
Fact Checker Agent     → verifies claims
        ↓
Quality Gate           → pass/fail check
        ↓
Final Content Output
```

**Current state (Phase 1):**

```
User Content Brief → Researcher Agent → Writer Agent → API Response
```

---

## Team

| Member | Responsibilities |
|--------|-----------------|
| Armaan | Crew architecture, Researcher Agent, Writer Agent, Editor Agent, SEO Agent, Fact Checker Agent, task dependency graph |
| Member 2 | Tavily integration, grammar checking, SEO keyword analyzer, plagiarism detection, quality gate, dashboard frontend, logging integrations |
| Member 3 | Human evaluation benchmark, client feedback agent, translation agent, content calendar agent, backend API integration, end-to-end testing, technical documentation |

---

## Tech Stack

**Backend**
- Python 3.12
- FastAPI + Uvicorn
- CrewAI + CrewAI Tools
- OpenAI API (gpt-4o)
- Tavily Search API
- Pydantic v2
- Loguru

**Frontend** *(Phase 2)*
- React + Vite + TypeScript
- TailwindCSS
- Axios
- Recharts
- Lucide React

---

## Project Structure

```
crewai-content-production-system/
│
├── backend/
│   ├── agents/
│   │   ├── researcher_agent.py     # Researcher — web search + summarization
│   │   ├── writer_agent.py         # Writer — article generation
│   │   ├── editor_agent.py         # TODO
│   │   ├── seo_agent.py            # TODO
│   │   └── fact_checker_agent.py   # TODO
│   │
│   ├── crews/
│   │   └── content_crew.py         # Wires agents + tasks, runs pipeline
│   │
│   ├── tasks/
│   │   └── content_tasks.py        # Task definitions for each agent
│   │
│   ├── tools/
│   │   ├── tavily_tool.py          # Tavily search wrapper
│   │   ├── grammar_tool.py         # TODO
│   │   ├── seo_tool.py             # TODO
│   │   └── plagiarism_tool.py      # TODO
│   │
│   ├── api/
│   │   └── routes.py               # FastAPI route definitions
│   │
│   ├── schemas/
│   │   ├── content_schema.py       # Input validation schema
│   │   └── response_schema.py      # Output response schema
│   │
│   ├── utils/
│   │   ├── logger.py               # Loguru structured logging
│   │   └── helpers.py              # Shared utilities
│   │
│   ├── workflows/
│   │   └── orchestration.py        # TODO
│   │
│   ├── logs/                       # Auto-generated log files
│   ├── tests/                      # TODO
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                       # TODO — Phase 2
│
├── docs/                           # TODO
├── README.md
├── .gitignore
└── docker-compose.yml              # TODO
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- OpenAI API key (with credits)
- Tavily API key (free tier at tavily.com)

### Setup

**1. Clone the repo**
```bash
git clone https://github.com/your-org/crewai-content-production-system.git
cd crewai-content-production-system
```

**2. Create and activate virtual environment**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your real API keys
```

**5. Start the server**
```bash
PYTHONPATH=. venv/bin/uvicorn main:app --reload --port 8000
```

**6. Open API docs**
```
http://localhost:8000/docs
```

---

## What's Built (Phase 1)

### ✅ Schemas
- `ContentBriefRequest` — validates user input (topic, tone, word count, audience)
- `ContentResponse` — structured API response (job_id, status, article, metadata)

### ✅ Tools
- `TavilySearchTool` — wraps Tavily Search API, returns typed search results

### ✅ Agents
- `ResearcherAgent` — searches web via Tavily, synthesizes research summary
- `WriterAgent` — generates article from research using OpenAI

### ✅ Tasks
- `build_research_task` — instructs Researcher Agent what to do
- `build_writing_task` — instructs Writer Agent with tone/word count/audience

### ✅ Crew
- `ContentCrew` — sequential pipeline: Researcher → Writer
- Async-safe execution via `run_in_executor`

### ✅ API
- `POST /api/v1/generate` — submit content brief, get article back
- `GET /api/v1/health` — health check

### ✅ Utilities
- Structured logging with Loguru (console + rotating JSON file)
- Job ID generation, timestamps, helpers

---

## API Reference

### POST `/api/v1/generate`

Submit a content brief to run the pipeline.

**Request body:**
```json
{
  "topic": "How AI is transforming healthcare diagnostics",
  "tone": "professional",
  "word_count": 800,
  "audience": "tech professionals"
}
```

| Field | Type | Required | Default | Options |
|-------|------|----------|---------|---------|
| topic | string | ✅ | — | 5–500 chars |
| tone | string | ❌ | professional | professional, casual, academic, persuasive |
| word_count | integer | ❌ | 800 | 200–3000 |
| audience | string | ❌ | general readers | any string |

**Success response:**
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "status": "success",
  "topic": "How AI is transforming healthcare diagnostics",
  "article": "Full article text...",
  "word_count": 823,
  "created_at": "2026-05-25T10:30:00Z",
  "error": null
}
```

### GET `/api/v1/health`

```json
{ "status": "ok" }
```

---

## Extended Features & APIs

The following APIs extend the core content generation pipeline with feedback, translation, calendar, and benchmarking capabilities (developed by Arya Gupta).

### Client Feedback API (US-19)

Allows clients to submit feedback on an existing article and trigger a revision run.

#### POST `/api/v1/feedback/submit`

Submit feedback to revise an existing article.

**Request body:**
```json
{
  "job_id": "job_xxx",
  "feedback": "Make the intro more engaging and add more statistics"
}
```

**Response:**
```json
{
  "feedback_job_id": "job_yyy",
  "status": "running",
  "original_job_id": "job_xxx",
  "created_at": "2026-06-02T10:00:00Z"
}
```

#### GET `/api/v1/feedback/jobs/{job_id}`

Get the status of a feedback revision job.

---

### Multilingual Translation API (US-20)

Translate an existing article into another language using an AI translation agent.

#### POST `/api/v1/translation/submit`

Submit a translation request for an existing article.

**Request body:**
```json
{
  "job_id": "job_xxx",
  "target_language": "Spanish"
}
```

**Supported languages:**
Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Russian, Turkish, Polish, Swedish

**Response:**
```json
{
  "translation_job_id": "job_yyy",
  "status": "running",
  "target_language": "Spanish",
  "created_at": "2026-06-02T10:00:00Z"
}
```

#### GET `/api/v1/translation/jobs/{job_id}`

Get the status and result of a translation job.

#### GET `/api/v1/translation/languages`

List all supported target languages.

---

### Content Calendar API (US-21)

Generate a structured content calendar for a given niche and audience.

#### POST `/api/v1/calendar/generate`

Generate a content calendar.

**Request body:**
```json
{
  "niche": "Tech Startups",
  "audience": "founders",
  "frequency": "weekly",
  "weeks": 4
}
```

**Response:**
```json
{
  "calendar_job_id": "job_yyy",
  "status": "running",
  "niche": "Tech Startups",
  "weeks": 4,
  "created_at": "2026-06-02T10:00:00Z"
}
```

#### GET `/api/v1/calendar/jobs/{job_id}`

Get the status and result of a calendar generation job.

---

### Human Evaluation Benchmark (US-18)

A benchmark harness that generates and evaluates articles across diverse topics, measuring quality, grammar, SEO performance, and generation time.

**Run the benchmark:**
```bash
cd backend
python -m utils.benchmark
```

The benchmark generates 3 articles on diverse topics and reports:
- Quality scores
- Grammar error counts
- SEO scores
- Generation times per article

---

## Running Tests

Navigate to the backend directory and run the test suite:

```bash
cd backend
python -m pytest tests/ -v
```

Alternatively, using unittest discovery:
```bash
python -m unittest discover tests/
```

**Test modules:**

| Module | Coverage |
|--------|----------|
| `test_api.py` | API route validation and responses |
| `test_e2e.py` | End-to-end pipeline tests |
| `test_quality_gate.py` | Quality gate pass/fail logic |
| `test_seo.py` | SEO scoring and keyword analysis |
| `test_grammar.py` | Grammar checking tool |
| `test_plagiarism.py` | Plagiarism detection tool |
| `test_tavily.py` | Tavily search integration |
| `test_job_store.py` | Job storage and retrieval |
| `test_doc_generator.py` | Document generation utilities |

---

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
TAVILY_API_KEY=tvly-...
LOG_LEVEL=DEBUG
APP_ENV=development
```

> ⚠️ Never commit `.env` — it is gitignored.

---

## Development Workflow

### Branch strategy
```
main          → stable, tested code only
armaan        → Armaan's work in progress
member2       → Member 2's work
member3       → Member 3's work
```

### Running locally
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. venv/bin/uvicorn main:app --reload --port 8000
```

### Testing a module in isolation
```bash
cd backend
PYTHONPATH=. python -c "from agents import build_researcher_agent; print(build_researcher_agent().role)"
```

---

## TODO / Remaining Work

### 🔴 Immediate (unblock Phase 1)

- [ ] **Add OpenAI credits** — pipeline hits 429 quota error without billing set up
- [ ] **Confirm end-to-end pipeline run** — one successful Researcher → Writer run
- [ ] **Fix venv environment** — ensure `venv/bin/uvicorn` is used consistently

### 🟡 Phase 1 Completion (Armaan)

- [ ] `agents/editor_agent.py` — refines tone, grammar, structure
- [ ] `agents/seo_agent.py` — adds keywords, meta description, headings
- [ ] `agents/fact_checker_agent.py` — verifies claims in the article
- [ ] Add Editor → SEO → Fact Checker to `content_tasks.py`
- [ ] Wire all 5 agents into `content_crew.py`
- [ ] Add `context` passing between tasks (research output → writer → editor)

### 🟡 Phase 1 Completion (Member 2)

- [ ] `tools/grammar_tool.py` — grammar and style checker
- [ ] `tools/seo_tool.py` — keyword density analyzer
- [ ] `tools/plagiarism_tool.py` — plagiarism detection
- [ ] Quality gate logic — pass/fail scoring on final article
- [ ] Logging integrations — connect log output to dashboard

### 🟡 Phase 1 Completion (Member 3)

- [ ] `backend/tests/` — unit tests for agents, tasks, crew
- [ ] End-to-end test script
- [ ] `docs/` — API documentation
- [ ] `backend/workflows/orchestration.py` — workflow state management

### 🔵 Phase 2 — Frontend

- [ ] Scaffold React + Vite + TypeScript app
- [ ] `ContentBriefForm` component — submit topic, tone, word count
- [ ] `ArticleDisplay` component — render generated article
- [ ] `WorkflowStatus` component — show which agent is running
- [ ] `Dashboard` page — job history, stats, charts (Recharts)
- [ ] Axios service layer — connect to FastAPI
- [ ] Loading states and error handling

### 🔵 Phase 3 — Advanced Features

- [ ] Translation Agent — multi-language output
- [ ] Client Feedback Agent — incorporate feedback into rewrites
- [ ] Content Calendar Agent — schedule and manage content
- [ ] Human evaluation benchmark
- [ ] PostgreSQL — persist jobs and articles
- [ ] Vector DB — semantic search over past content
- [ ] Docker Compose — containerize backend + frontend
- [ ] Streaming API — real-time agent output to frontend

---

## Roadmap

```
Phase 1 (Current)
  ✅ Project architecture
  ✅ Researcher Agent + Writer Agent
  ✅ FastAPI pipeline
  ⏳ Editor + SEO + Fact Checker agents
  ⏳ Quality gate
  ⏳ First full end-to-end run

Phase 2
  ⏳ React frontend
  ⏳ Dashboard + workflow visualization
  ⏳ Logging UI

Phase 3
  ⏳ Translation + Feedback + Calendar agents
  ⏳ Database persistence
  ⏳ Docker deployment
```

---

> Built as a capstone project demonstrating multi-agent orchestration, AI workflow engineering, and production-grade backend architecture.