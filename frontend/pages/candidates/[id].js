import Link from "next/link";
import { useEffect, useState } from "react";
import AuditLog from "../../components/AuditLog";
import { getAuditLogs, getCandidateHistory, getCandidates } from "../../lib/api";

function valueOrFallback(value, fallback = "Not provided") {
  return value || fallback;
}

const STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"];

function getNextStage(current) {
  const idx = STAGES.findIndex((s) => s.toLowerCase() === current?.toLowerCase());
  if (idx === -1) return STAGES[0];
  if (idx === STAGES.length - 1) return current;
  return STAGES[idx + 1];
}

function formatLogEntries(logs = []) {
  return logs.map((log) => ({
    ...log,
    title: log.action || log.title,
    details: log.metadata || log.details || "No additional details.",
  }));
}

export async function getServerSideProps({ params }) {
  try {
    const candidatesPayload = await getCandidates();

    let candidates = [];
    if (Array.isArray(candidatesPayload)) {
      candidates = candidatesPayload;
    } else if (typeof candidatesPayload === "object" && candidatesPayload !== null) {
      candidates = Object.values(candidatesPayload).flat();
    }

    const candidate = candidates.find(
      (item) => String(item.id ?? item.candidate_id) === String(params.id)
    );

    if (!candidate) return { notFound: true };

    const [historyPayload, auditLogs] = await Promise.all([
      getCandidateHistory(params.id),
      getAuditLogs(params.id),
    ]);

    return {
      props: {
        candidate,
        initialAuditLogs: formatLogEntries(auditLogs ?? []),
        initialStage: historyPayload?.current_stage ?? candidate.stage ?? "Unstaged",
        initialDaysInStage: historyPayload?.days_in_stage ?? 0,
      },
    };
  } catch {
    return {
      props: {
        candidate: null,
        initialAuditLogs: [],
        initialStage: "Unstaged",
        initialDaysInStage: 0,
        initialError: true,
      },
    };
  }
}

export default function CandidateDetail({
  candidate: initialCandidate,
  initialAuditLogs = [],
  initialStage = "Unstaged",
  initialDaysInStage = 0,
  initialError = false,
}) {
  const [candidate] = useState(initialCandidate);
  const [auditLogs, setAuditLogs] = useState(initialAuditLogs);
  const [stage, setStage] = useState(initialStage);
  const [daysInStage, setDaysInStage] = useState(initialDaysInStage);
  const [error, setError] = useState(initialError);

  const id = candidate?.id ?? candidate?.candidate_id;

  useEffect(() => {
    if (!id) return;
    let active = true;

    Promise.all([getCandidateHistory(id), getAuditLogs(id)])
      .then(([nextHistoryPayload, nextAuditLogs]) => {
        if (!active) return;
        setStage(nextHistoryPayload?.current_stage ?? "Unstaged");
        setDaysInStage(nextHistoryPayload?.days_in_stage ?? 0);
        setAuditLogs(formatLogEntries(nextAuditLogs ?? []));
        setError(false);
      })
      .catch(() => active && setError(true));

    return () => {
      active = false;
    };
  }, [id]);

  const name = candidate?.name || candidate?.full_name || "Unnamed candidate";
  const email = candidate?.email || candidate?.email_address;
  const role = candidate?.role || candidate?.position || candidate?.job_title;

  async function updateStage(newStage) {
    try {
      await fetch(`/api/backend/hiring/candidates/${id}/stage`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_stage: newStage }),
      });

      const [nextHistoryPayload, nextAuditLogs] = await Promise.all([
        getCandidateHistory(id),
        getAuditLogs(id),
      ]);

      setStage(nextHistoryPayload?.current_stage ?? newStage);
      setDaysInStage(nextHistoryPayload?.days_in_stage ?? 0);
      setAuditLogs(formatLogEntries(nextAuditLogs ?? []));
      setError(false);
    } catch {
      setError(true);
    }
  }

  function handleAdvanceStage() {
    const nextStage = getNextStage(stage);
    updateStage(nextStage);
  }

  function handleRejectCandidate() {
    updateStage("Rejected");
  }

  const isTerminalStage = stage === "Rejected" || stage === "Hired";

  return (
    <main className="page-shell">
      <header className="topbar">
        <Link href="/" className="brand">
          <span className="brand__mark">M</span>
          Mini Hiring Pipeline
        </Link>
        <nav className="topbar__nav" aria-label="Main navigation">
          <Link href="/">Dashboard</Link>
          <Link href="/search">Search</Link>
        </nav>
        <div className="status-pill">
          <span className="status-dot" />
          Backend connected
        </div>
      </header>

      <Link className="back-link" href="/">
        ← Back to Dashboard
      </Link>

      <section className="profile-header">
        <div className="profile-avatar">
          {name
            .split(" ")
            .map((part) => part[0])
            .slice(0, 2)
            .join("")
            .toUpperCase()}
        </div>
        <div className="profile-header__main">
          <p className="eyebrow">Candidate profile</p>
          <h1>{name}</h1>
          <p className="profile-header__subtitle">
            {valueOrFallback(role)} {email ? `· ${email}` : ""}
          </p>
        </div>
        <span className="stage-pill">{stage}</span>
        <span className="stage-pill days-pill">Days in stage: {daysInStage}</span>

        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={handleAdvanceStage}
            className="button"
            disabled={isTerminalStage}
          >
            Move to Next Stage
          </button>
          <button
            onClick={handleRejectCandidate}
            className="button button--danger"
            style={{ backgroundColor: "#dc2626", color: "#ffffff" }}
            disabled={isTerminalStage}
          >
            Reject
          </button>
        </div>
      </section>

      {error && (
        <div className="alert">
          Some activity could not be refreshed. Showing the latest available data.
        </div>
      )}

      {/* Single Activity Log Card */}
      <section className="detail-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Audit trail</p>
            <h2>Activity log</h2>
          </div>
          <span className="result-count">{auditLogs.length} entries</span>
        </div>
        <AuditLog logs={auditLogs} />
      </section>
    </main>
  );
}