# Mini Hiring Pipeline Frontend

A Next.js recruiting dashboard for tracking candidates through the hiring pipeline, searching across applicants, and reviewing audit activity.

## Overview

This frontend app connects to a FastAPI backend and presents:

- A Kanban-style Dashboard
- Candidate search and filtering
- Candidate detail pages
- Audit log viewing
- Add-candidate form workflow

## Tech Stack

- Next.js
- React
- JavaScript
- FastAPI backend integration via API rewrites

## Project Structure

```text
.
├── components/
│   ├── AuditLog.js
│   ├── CandidateCard.js
│   ├── KanbanBoard.js
│   └── SearchBox.js
├── lib/
│   └── api.js
├── pages/
│   ├── _app.js
│   ├── index.js
│   ├── search.js
│   └── candidates/
│       └── [id].js
├── styles/
│   └── globals.css
├── next.config.js
├── package.json
└── README.md
```

## Prerequisites

Before running this app, make sure you have:

- Node.js 18+ installed
- npm installed
- A working FastAPI backend running on port 8000, or a custom backend URL configured via environment variables

## Installation

```bash
npm install
```

## Configuration

The app expects a backend at:

```text
http://127.0.0.1:8000
```

You can override it by setting the environment variable:

```bash
BACKEND_URL=http://127.0.0.1:8000 npm run dev
```

## Run the App

Development mode:

```bash
npm run dev
```

Then open:

```text
http://localhost:3000
```

Production build:

```bash
npm run build
npm run start
```

## Available Scripts

```bash
npm run dev     # start development server
npm run build   # create production build
npm run start   # run production server
npm run lint    # run Next.js lint checks
```

## Backend Expectations

This frontend calls backend routes such as:

- `/hiring/candidates`
- `/hiring/search`
- `/hiring/candidates/:id/history`
- `/hiring/audit_logs`

The `next.config.js` rewrite forwards requests from `/api/backend/*` to the configured backend URL.

## Notes

- If the backend is not running, the dashboard may show an error state.
- The app is designed to work as a recruiter-facing pipeline dashboard for candidate management.

## License

This project is for educational or internal development use unless otherwise specified.
