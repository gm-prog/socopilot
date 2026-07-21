import { useState } from "react";
import { Link } from "react-router-dom";
import { semanticSearch } from "../api/alerts";
import { useAuth } from "../context/AuthContext";
import { EliteCard } from "../components/EliteCard";

export default function Search() {
  const { isAuthenticated } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!isAuthenticated) {
      setError("Authentication required. Please sign in to run semantic search.");
      return;
    }

    try {
      setError(null);
      const data = await semanticSearch(query);
      setResults(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    }
  };

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-serif text-heritage-gold tracking-wide mb-2">Semantic Intelligence</h2>
        <p className="text-heritage-muted text-sm font-sans tracking-widest uppercase">
          Cosine similarity analysis over stored alert embeddings
        </p>
      </div>

      {!isAuthenticated && (
        <div className="mb-6 rounded-3xl border border-heritage-goldBorder/30 bg-heritage-ink/90 p-6 text-sm text-heritage-text">
          <p className="mb-3">You must be signed in to use semantic search.</p>
          <Link
            to="/login"
            className="inline-flex items-center justify-center rounded-full border border-heritage-gold/30 bg-heritage-gold/5 px-6 py-2.5 text-sm uppercase tracking-[0.28em] text-heritage-gold transition hover:bg-heritage-gold/15"
          >
            Sign in
          </Link>
        </div>
      )}

      <EliteCard className="p-6 mb-6">
        <div className="flex flex-col gap-4 sm:flex-row">
          <input
            className="flex-1 rounded-3xl border border-heritage-goldBorder/30 bg-heritage-ink/90 px-4 py-3 text-sm text-heritage-text font-sans focus:border-heritage-gold/50 focus:outline-none transition-colors duration-400 ease-premium placeholder-heritage-muted/50"
            placeholder="Describe similar threats..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={!isAuthenticated}
          />
          <button
            type="button"
            onClick={run}
            className="rounded-full border border-heritage-gold/30 bg-heritage-gold/5 px-6 py-3 text-sm font-sans uppercase tracking-widest text-heritage-gold transition hover:bg-heritage-gold/15 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!isAuthenticated}
          >
            Search
          </button>
        </div>
      </EliteCard>

      {error && (
        <div className="rounded-3xl border border-heritage-burgundy/30 bg-heritage-burgundy/10 px-6 py-4 text-sm font-sans tracking-wide mb-6">
          <span className="text-heritage-burgundy">{error}</span>
        </div>
      )}

      {results != null && (
        <EliteCard className="p-6 overflow-auto">
          <pre className="text-xs font-mono text-heritage-text whitespace-pre-wrap">
            {JSON.stringify(results, null, 2)}
          </pre>
        </EliteCard>
      )}
    </div>
  );
}
