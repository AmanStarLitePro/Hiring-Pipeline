import Link from "next/link";
import { useEffect, useState } from "react";
import KanbanBoard from "../components/KanbanBoard";
import { getCandidates } from "../lib/api";

export async function getServerSideProps() {
  try {
    return { props: { initialCandidates: await getCandidates() } };
  } catch {
    return { props: { initialCandidates: [], initialError: true } };
  }
}

export default function Dashboard({
  initialCandidates = [],
  initialError = false,
}) {
  const [candidates, setCandidates] = useState(initialCandidates);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(initialError);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getCandidates()
      .then((data) => {
        if (active) {
          setCandidates(data);
          setError(false);
        }
      })
      .catch(() => active && setError(true))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="page-shell">
      <header className="topbar">
        <Link href="/" className="brand">
          <span className="brand__mark">M</span>
          Mini Hiring Pipeline
        </Link>
        <nav className="topbar__nav" aria-label="Main navigation">
          <Link className="active" href="/">
            Dashboard
          </Link>
          <Link href="/search">Search</Link>
        </nav>
        <div className="status-pill">
          <span className="status-dot" />
          Backend connected
        </div>
      </header>

      <section className="page-intro">
        <div>
          <p className="eyebrow">Recruiting pipeline</p>
          <h1>Candidate overview</h1>
          <p className="page-intro__description">
            Keep every candidate and next step visible in one place.
          </p>
        </div>
        <Link className="button button--dark" href="/search">
          Find candidates <span aria-hidden="true">↗</span>
        </Link>
      </section>

      {error && (
        <div className="alert">
          Could not reach FastAPI. Start the backend at{" "}
          <code>127.0.0.1:8000</code> and refresh.
        </div>
      )}

      <div className="board-toolbar">
        <span>
          {candidates.length} candidate{candidates.length === 1 ? "" : "s"}
        </span>
        {loading && <span className="muted">Refreshing...</span>}
      </div>
      <KanbanBoard candidates={candidates} />
    </main>
  );
}