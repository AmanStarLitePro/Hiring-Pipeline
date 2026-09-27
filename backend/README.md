# Mini Hiring Pipeline Backend

A FastAPI-based hiring pipeline backend for managing candidate records, tracking interview stages, and performing semantic search over hiring data using a RAG-style workflow with Cassandra and FAISS.

## Overview

This project provides a lightweight backend for:

- Adding and listing candidates
- Moving candidates through pipeline stages
- Rejecting candidates
- Fetching candidate history and audit logs
- Searching candidate records using a natural-language query
- Storing and querying hiring data in Cassandra

The service is built with:

- Python
- FastAPI
- Cassandra
- FAISS
- LangChain + Groq
- Docker Compose for local infrastructure

## Project Structure

```text
Mini_hiring_pipeline_backend/
├── artifacts/
│   └── schema.json
├── log_info/
├── notebooks/
│   └── research.ipynb
├── src/
│   └── hiring_pipeline/
│       ├── __init__.py
│       ├── exception.py
│       ├── logger_config.py
│       ├── api/
│       │   ├── dependencies.py
│       │   ├── server.py
│       │   └── routers/
│       │       └── hiring.py
│       ├── components/
│       │   └── CRUD_functions.py
│       ├── pipelines/
│       │   ├── database_pipeline.py
│       │   ├── initialize_schema.py
│       │   └── RAG_pipeline.py
│       └── utils/
│           └── cassandra_utils.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Features

### Candidate management
- Add a new candidate
- Group candidates by pipeline stage
- Move candidates to the next stage
- Reject a candidate from the pipeline
- View candidate stage history and audit trail

### Hiring workflow stages
The pipeline is defined in the application as:

```text
Applied -> Screening -> Interview -> Offer -> Hired
```

### Search and RAG pipeline
The backend includes a semantic search flow that:

- loads candidate data from Cassandra
- creates embeddings for candidate names and metadata
- searches using FAISS
- constructs a recruiter-style prompt for the LLM
- returns structured search results via Groq

## Tech Stack

- FastAPI for REST endpoints
- Cassandra for persistent storage
- FAISS for vector similarity search
- SentenceTransformers for embeddings
- LangChain Groq integration for LLM-powered search
- Docker Compose for local database setup

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+
- pip
- Docker Desktop or Docker Engine
- A Groq API key for the LLM search flow

## Environment Variables

For not making this very much complicated
i have added a sample .env which contains temporary api keys

Create a `.env` file in the project root with values similar to:

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
```

Notes:
- Cassandra is started through Docker Compose.
- The backend auto-creates the keyspace if it does not exist.
- The RAG search endpoint depends on a valid Groq API key.

## Installation

1. Clone the repository
2. Navigate to the project folder
3. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

4. Install dependencies

```bash
pip install -r requirements.txt
```

## Running Cassandra

Start the Cassandra container using Docker Compose:

```bash
docker-compose up -d
```

This will expose Cassandra on port `9042`.

## Initializing the Database Schema

The schema is defined in `artifacts/schema.json` and can be initialized with:

```bash
python -m src.hiring_pipeline.pipelines.initialize_schema
```

This script creates the keyspace and tables if they do not already exist, then inserts sample data.

## Running the API

From the project root:

```bash
uvicorn src.hiring_pipeline.api.server:app --reload --host 0.0.0.0 --port 8000
```

You can also run the file directly:

```bash
python src/hiring_pipeline/api/server.py
```

## API Endpoints

### Search candidates

```http
POST /hiring/search
```

Request body:

```json
{
  "query": "Find candidates with strong interview backgrounds"
}
```

### Add candidate

```http
POST /hiring/candidates
```

Request body:

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

### Get all candidates grouped by stage

```http
GET /hiring/candidates
```

### Move candidate to next stage

```http
PATCH /hiring/candidates/{candidate_id}/stage
```

Example body:

```json
{
  "new_stage": "Interview"
}
```

### Reject candidate

```http
PATCH /hiring/candidates/{candidate_id}/stage
```

Body:

```json
{
  "new_stage": "Rejected"
}
```

### Candidate history

```http
GET /hiring/candidates/{candidate_id}/history
```

### Audit logs

```http
GET /hiring/audit_logs
```

Optional query parameter:

```http
GET /hiring/audit_logs?candidate_id={candidate_id}
```

## Example Requests

Using `curl`:

```bash
curl -X POST "http://localhost:8000/hiring/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Search for Aman"}'
```

```bash
curl -X POST "http://localhost:8000/hiring/candidates" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com"}'
```

```bash
curl "http://localhost:8000/hiring/candidates"
```

## Notes

- This backend is designed as a local prototype and starter project for a hiring pipeline.
- The RAG search uses a Groq LLM and FAISS embeddings to help find relevant candidates based on natural-language queries.
- Cassandra is a core dependency for the persistent hiring data model.

## Troubleshooting

### Cassandra connection errors
Ensure Docker is running and the Cassandra container is active:

```bash
docker-compose ps
```

### Groq search not working
Check that the `GROQ_API_KEY` environment variable is valid and available in your shell or `.env` file.

### Missing schema or tables
Run:

```bash
python -m src.hiring_pipeline.pipelines.initialize_schema
```
