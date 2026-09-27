import { useState } from "react";

export default function SearchBox({ onSearch, loading = false }) {
  const [query, setQuery] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (trimmedQuery) onSearch(trimmedQuery);
  }

  return (
    <form className="search-box" onSubmit={handleSubmit}>
      <label htmlFor="recruiter-query">Search candidates</label>
      <div className="search-box__row">
        <input
          id="recruiter-query"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Try: Who's in Interview right now?"
          aria-label="Recruiter search query"
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>
      <p className="search-box__hint">
        Ask to search across your candidate database.
      </p>
    </form>
  );
}