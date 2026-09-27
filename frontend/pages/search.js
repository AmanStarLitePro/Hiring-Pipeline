import Link from "next/link";
import { useState } from "react";
import CandidateCard from "../components/CandidateCard";
import SearchBox from "../components/SearchBox";
import { searchCandidates } from "../lib/api";

export default function SearchPage() {
  const [results, setResults] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(nextQuery) {
    setQuery(nextQuery);
    setLoading(true);
    setError("");
    try {
      const response = await searchCandidates(nextQuery);
      
      const records = Array.isArray(response)
        ? response
        : response?.records && Array.isArray(response.records)
        ? response.records
        : [];

      setResults(records);
    } catch (requestError) {
      setError(requestError.message || "Search failed. Please try again.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  const hasReason = results.length > 0 && typeof results[0]?.reason === "string";
  const reasonText = hasReason ? results[0].reason : null;

  return (
    <main className="page-shell">
      <header className="topbar">
        <Link href="/" className="brand">
          <span className="brand__mark">M</span>
          Mini Hiring Pipeline
        </Link>
        <nav className="topbar__nav" aria-label="Main navigation">
          <Link href="/">Dashboard</Link>
          <Link className="active" href="/search">
            Search
          </Link>
        </nav>
        <div className="status-pill">
          <span className="status-dot" />
          Backend connected
        </div>
      </header>

      <section className="search-hero">
        <p className="eyebrow">Recruiting the best talent</p>
        <h1>AI Based Search</h1>
        <p>
          Ask in plain language. Your AI Based search turns the query
          into a focused candidate shortlist.
        </p>
        <SearchBox onSearch={handleSearch} loading={loading} />
      </section>

      {error && <div className="alert">{error}</div>}

      {query && !loading && (
        <section className="search-results">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Results for</p>
              <h2>&ldquo;{query}&rdquo;</h2>
            </div>
            <span className="result-count">
              {hasReason ? "0 matches" : `${results.length} matches`}
            </span>
          </div>

          {hasReason ? (
            <div className="empty-state">
              <h3>No candidates matched your request</h3>
              <p className="reason-text">{reasonText}</p>
            </div>
          ) : results.length > 0 ? (
            <div className="results-grid">
              {results.map((candidate, index) => (
                <CandidateCard
                  candidate={candidate}
                  key={candidate.id ?? candidate.candidate_id ?? index}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <h3>No candidates found</h3>
              <p>Try broadening your query.</p>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
