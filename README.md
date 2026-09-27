# Mini Hiring Pipeline

A full-stack recruiting workflow built to help a recruiter manage candidates through a hiring pipeline and answer natural-language hiring questions quickly.

## Project Goal

A recruiter manages candidates for one job. Each candidate moves through the stages:

Applied → Screening → Interview → Offer → Hired

A candidate may also be rejected at any point before being hired. The app helps the recruiter:

- add candidates and see everyone grouped by current stage
- move candidates forward one stage at a time
- prevent invalid stage jumps or reversing final outcomes
- open a candidate and review their complete audit trail and time-in-stage history
- search for candidates using natural-language queries

## Expected Project Outcome:

### Managing the pipeline

- Add candidates and see groups by current stage
- Move candidates along the pipeline without skipping stages
- Prevent reverse movement or invalid transitions after final decisions
- Open a candidate profile and view complete history, including how long the candidate has been in the current stage
- Preserve history as an immutable audit trail

### Finding candidates

The recruiter should be able to ask questions such as:

- "Find Priya Sharma" even when typing "sharam"
- "Who is in Interview right now?"
- "Who has been stuck in Screening for more than a week?"
- "Who moved to Interview since Monday?"
- "Who reached the Offer stage but didn't get hired?"
- "Everyone except rejected candidates."

The search should combine conditions, rank the strongest matches first, and return meaningful feedback instead of a silent empty list when the query is unclear.

## Deliverables

This project was built to satisfy the core hiring-pipeline requirement set, including:

- a candidate pipeline dashboard
- stage progression workflow with validation rules
- searchable candidate data and natural-language retrieval
- audit/history tracking for every action
- a final architecture summary and run instructions
- AI-assisted development process with human review and one documented disagreement

## Application Architecture

The system is split into a frontend dashboard and a backend service:

```text
+-------------------+        +---------------------------+
| Next.js Frontend  | <----> | FastAPI Backend           |
| - Kanban board    |        | - Candidate CRUD          |
| - Candidate view  |        | - Stage transitions       |
| - Search UI       |        | - Audit logs              |
| - Recruiter flow  |        | - Search/RAG endpoint     |
+-------------------+        +---------------------------+
          |                              |
          |                              v
          |                    +-------------------+
          |                    | Cassandra + FAISS |
          |                    | vector + storage  |
          |                    +-------------------+
          |
          v
   Browser-based recruiter dashboard
```

### Frontend

Built with:

- Next.js
- React
- JavaScript
- server-side data fetching and API rewrites

Features:

- Kanban candidate board
- candidate search page
- candidate detail/history views
- add-candidate form
- recruiter-friendly UI

### Backend

Built with:

- FastAPI
- Cassandra for persistent storage
- FAISS for vector similarity search
- LangChain + Groq for AI-powered candidate retrieval
- schema initialization and audit logic

The backend exposes endpoints such as:

- `POST /hiring/search`
- `POST /hiring/candidates`
- `GET /hiring/candidates`
- `PATCH /hiring/candidates/{candidate_id}/stage`
- `GET /hiring/candidates/{candidate_id}/history`
- `GET /hiring/audit_logs`

## Tech Stack

### Frontend

- Next.js
- React
- JavaScript

### Backend

- Python
- FastAPI
- Cassandra
- FAISS
- LangChain
- Groq
- Docker

## Prerequisites

Before running the project, ensure you have:

- Node.js 18+
- npm
- Python 3.10+
- pip
- Docker Desktop or Docker Engine
- a valid Groq API key for semantic search
- a valid Hugging Face API key for index based similarity search

## Environment Variables

Create a `.env` file in the backend project root (`backend/.env`) with values like:

```env
CASSANDRA_HOST=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=mini_hiring_pipeline
CASSANDRA_USERNAME=Username
CASSANDRA_PASSWORD=Password
PORT=8000
WORKERS=2
ENVIRONMENT=development
GROQ_API_KEY=groq_api_key
HF_TOKEN=hugging_face_api_key
```

## Running the Frontend

From the repo root:

```bash
cd frontend
npm install
npm run dev
```

Open the app in the browser:

```text
http://localhost:3000
```

## Running the Backend

From the repo root:

```bash
cd backend
```

1. Start Cassandra using Docker Compose:

```bash
docker-compose up -d
```

2. Create and activate a virtual environment:

```bash
py -3.10 -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

3. Install backend dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database schema:

```bash
python -m src.hiring_pipeline.pipelines.initialize_schema
```

5. Run the API server:

```bash
uvicorn src.hiring_pipeline.api.server:app --reload --host 0.0.0.0 --port 8000
```

### Running both services together

Open two terminals:

- Terminal 1: start the backend in `backend/`
- Terminal 2: start the frontend in `frontend/`

This lets the recruiter dashboard call the FastAPI API at `http://127.0.0.1:8000` while the UI runs on `http://localhost:3000`.

## Core Features

### Candidate pipeline

- Add candidates to the system
- Display all candidates grouped by pipeline stage
- Advance candidates from one stage to the next
- Enforce valid transitions only
- Track audit history for every candidate action

### Candidate history and audit trail

Every stage move is recorded as a history event, allowing the recruiter to answer:

- how long a candidate has been in a stage
- when they moved to interview or offer
- whether they were rejected or hired
- what sequence of events led to the current outcome

### Search experience

The search workflow is designed to support both structured and conversational queries. It uses candidate metadata, history, and embedding-based matching so searches like "sharam" still resolve to the correct candidate.

## Design Decisions and Why

### 1. Frontend + backend split

The frontend was kept separate from the backend so that the recruiter experience can change independently of data and search logic. This makes the UI easier to maintain while the pipeline logic remains centralized in the API.

### 2. Stage validation rules

The system enforces a clear pipeline progression instead of allowing arbitrary stage changes. This is important because recruiting stages are not random; they form a process with business rules.

### 3. Immutable audit trail

Candidate history is treated as a permanent record. Once an action is recorded, it cannot be altered. This is aligned with recruiter needs and supports trustworthy compliance and traceability.

### 4. Semantic / fuzzy search

Exact search is not enough for recruiter workflows. People often type partial, misspelled, or conversational queries. A fuzzy or semantic retrieval layer improves discoverability and makes the app feel natural to use.

### 5. Vector search with Cassandra backing

This architecture allows the app to store structured hiring data reliably while still enabling AI-assisted search and ranking. Cassandra provides persistence, and FAISS allows fast similarity search over candidate data and metadata.

## What I Would Do With More Time

- add stricter role-based permissions for recruiter and hiring manager views
- improve the candidate detail page with resume parsing and notes
- add richer filtering for date windows, stage durations, and rejection reasons
- implement more robust ranking and search semantics for natural-language recruiter questions
- add automated tests for stage transitions, history correctness, and search behavior
- create a deployment pipeline and production configuration for Kubernetes or Docker Swarm

## AI Collaboration Notes

AI tools were used to accelerate project scaffolding, API route design, and iteration on the recruiting workflow. One notable place where human review was necessary was the search strategy:

- The AI initially suggested a simple literal matching approach for queries like "sharam".
- I disagreed with that because recruiter queries often include spelling variations, partials, and natural-language intent.
- The final approach favors fuzzy/semantic matching and ranking so that the strongest matches are surfaced first, and poor queries still return a meaningful explanation rather than an empty result.

This was an important design correction, because the problem is not only "searching for a string", but understanding the recruiter’s intent in a hiring workflow.
