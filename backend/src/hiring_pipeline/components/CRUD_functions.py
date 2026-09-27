from fastapi import APIRouter
import uuid, datetime
from cassandra.cluster import Session

def add_candidate(name: str, email: str, session: Session):
    candidate_id = uuid.uuid4()
    created_at = datetime.datetime.utcnow()

    session.execute(
        """
        INSERT INTO candidates (id, name, email, current_stage, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (candidate_id, name, email, "Applied", created_at)
    )

    session.execute(
        """
        INSERT INTO stages (candidate_id, stage_name, entered_at)
        VALUES (%s, %s, %s)
        """,
        (candidate_id, "Applied", created_at)
    )

    session.execute(
        """
        INSERT INTO audit_log (log_id, candidate_id, action, timestamp, metadata)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (uuid.uuid4(), candidate_id, "Candidate added", created_at, "Initial insert")
    )

    return {"id": str(candidate_id), "name": name, "email": email, "stage": "Applied"}

def get_candidates_grouped(session: Session):
    rows = session.execute("SELECT id, name, email, current_stage FROM candidates")
    grouped = {}
    for row in rows:
        grouped.setdefault(row.current_stage, []).append({
            "id": str(row.id),
            "name": row.name,
            "email": row.email
        })
    return grouped

pipeline = ["Applied", "Screening", "Interview", "Offer", "Hired"]

def move_stage(candidate_id: str, session: Session):
    try:
        candidate_uuid = uuid.UUID(candidate_id)
    except ValueError:
        return {"error": "Invalid UUID format"}

    candidate = session.execute(
        "SELECT current_stage FROM candidates WHERE id=%s", (candidate_uuid,)
    ).one()

    if not candidate:
        return {"error": "Candidate not found"}

    current_stage = candidate.current_stage
    if current_stage in ["Rejected", "Hired"]:
        return {"error": "Cannot move candidate after final outcome"}

    try:
        next_stage = pipeline[pipeline.index(current_stage) + 1]
    except (ValueError, IndexError):
        return {"error": "Invalid stage transition"}

    now = datetime.datetime.utcnow()

    session.execute(
        "UPDATE candidates SET current_stage=%s WHERE id=%s",
        (next_stage, uuid.UUID(candidate_id))
    )

    session.execute(
        "INSERT INTO stages (candidate_id, stage_name, entered_at) VALUES (%s, %s, %s)",
        (uuid.UUID(candidate_id), next_stage, now)
    )

    session.execute(
        "INSERT INTO audit_log (log_id, candidate_id, action, timestamp, metadata) VALUES (%s, %s, %s, %s, %s)",
        (uuid.uuid4(), uuid.UUID(candidate_id), f"Moved to {next_stage}", now, "Stage transition")
    )

    return {"id": candidate_id, "new_stage": next_stage}

def reject_candidate(candidate_id: str, session: Session):
    try:
        candidate_uuid = uuid.UUID(candidate_id)
    except ValueError:
        return {"error": "Invalid UUID format"}

    candidate = session.execute(
        "SELECT current_stage FROM candidates WHERE id=%s", (candidate_uuid,)
    ).one()

    if not candidate:
        return {"error": "Candidate not found"}

    if candidate.current_stage in ["Rejected", "Hired"]:
        return {"error": "Cannot change stage after final outcome"}

    now = datetime.datetime.utcnow()

    session.execute(
        "UPDATE candidates SET current_stage=%s WHERE id=%s",
        ("Rejected", candidate_uuid)
    )

    session.execute(
        "INSERT INTO stages (candidate_id, stage_name, entered_at) VALUES (%s, %s, %s)",
        (candidate_uuid, "Rejected", now)
    )

    session.execute(
        "INSERT INTO audit_log (log_id, candidate_id, action, timestamp, metadata) VALUES (%s, %s, %s, %s, %s)",
        (uuid.uuid4(), candidate_uuid, "Candidate Rejected", now, "Stage transition")
    )

    return {"id": candidate_id, "new_stage": "Rejected"}

def get_history(candidate_id: str, session: Session):
    logs = session.execute(
        "SELECT action, timestamp, metadata FROM audit_log WHERE candidate_id=%s",
        (uuid.UUID(candidate_id),)
    )
    history = []
    for log in logs:
        history.append({
            "action": log.action,
            "timestamp": log.timestamp,
            "metadata": log.metadata
        })

    stage = session.execute(
        "SELECT stage_name, entered_at FROM stages WHERE candidate_id=%s ORDER BY entered_at DESC LIMIT 1 ALLOW FILTERING",
        (uuid.UUID(candidate_id),)
    ).one()
    if stage:
        duration = (datetime.datetime.utcnow() - stage.entered_at).days
    else:
        duration = None

    return {"history": history, "current_stage": stage.stage_name if stage else None, "days_in_stage": duration}

def get_audit_logs(session: Session, candidate_id: str = None, reverse: bool = True):
    if candidate_id:
        logs = session.execute("SELECT * FROM audit_log WHERE candidate_id=%s", (uuid.UUID(candidate_id),))
    else:
        logs = session.execute("SELECT * FROM audit_log")

    log_list = [
        {
            "log_id": str(log.log_id),
            "candidate_id": str(log.candidate_id),
            "action": log.action,
            "timestamp": log.timestamp,
            "metadata": log.metadata
        }
        for log in logs
    ]

    log_list.sort(
        key=lambda item: item["timestamp"] if item["timestamp"] is not None else datetime.datetime.min,
        reverse=reverse
    )

    return log_list