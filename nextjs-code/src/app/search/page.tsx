"use client";

import Link from "next/link";
import { useState, useCallback, useRef } from "react";
import { MAX_CHARS, HARRY_POTTER_BOOKS } from "@/lib/sample-data";
import { ingestDocument, deleteDocument, searchDocuments, type SearchResult } from "@/lib/api";


type SearchMode = "vector" | "bm25" | "hybrid";
type ResultLimit = 5 | 10 | 20;


function BackButton() {
  return (
    <Link
      href="/"
      className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors duration-200"
      style={{ color: "var(--text-secondary)" }}
      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m15 18-6-6 6-6" />
      </svg>
      Back
    </Link>
  );
}


export default function SearchPage() {
  const [content, setContent] = useState("");
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [limit, setLimit] = useState<ResultLimit>(10);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [sampleLoaded, setSampleLoaded] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track the ingested doc_id for custom text
  const docIdRef = useRef<string | null>(null);

  const charCount = content.length;
  const isOverLimit = charCount > MAX_CHARS;


  /**
   * Ingest custom text if not yet ingested, then search.
   * Sample data skips ingestion (already in backend).
   */
  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setError(null);

    try {
      // If custom text and not yet ingested, ingest first
      if (!sampleLoaded && content.trim() && !docIdRef.current) {
        setIsIngesting(true);
        const { doc_id } = await ingestDocument("Custom Content", content);
        docIdRef.current = doc_id;
        setIsIngesting(false);
      }

      // Build scope
      const scope = sampleLoaded
        ? { source: "sample" }
        : { doc_id: docIdRef.current! };

      setIsSearching(true);
      const found = await searchDocuments(query, mode, limit, scope);
      setResults(found);
      setHasSearched(true);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsSearching(false);
      setIsIngesting(false);
    }
  }, [content, query, mode, limit, sampleLoaded]);


  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearch();
    }
  };


  const handleLoadSample = () => {
    // Clear any previously ingested custom doc
    if (docIdRef.current) {
      deleteDocument(docIdRef.current);
      docIdRef.current = null;
    }
    setSampleLoaded(true);
    setResults([]);
    setHasSearched(false);
    setError(null);
  };


  const handleClear = async () => {
    // Clean up ingested doc on the backend
    if (docIdRef.current) {
      await deleteDocument(docIdRef.current);
      docIdRef.current = null;
    }
    setContent("");
    setSampleLoaded(false);
    setResults([]);
    setHasSearched(false);
    setError(null);
  };


  const handleClearSample = () => {
    setSampleLoaded(false);
    setContent("");
    setResults([]);
    setHasSearched(false);
    setError(null);
  };


  // When content changes, invalidate old ingestion
  const handleContentChange = (val: string) => {
    if (docIdRef.current) {
      deleteDocument(docIdRef.current);
      docIdRef.current = null;
    }
    setContent(val);
    setResults([]);
    setHasSearched(false);
  };


  const modes: { value: SearchMode; label: string }[] = [
    { value: "vector", label: "Vector" },
    { value: "bm25", label: "BM25" },
    { value: "hybrid", label: "Combined" },
  ];

  const limits: ResultLimit[] = [5, 10, 20];

  const hasContent = sampleLoaded || content.trim().length > 0;


  return (
    <div className="flex flex-1 flex-col h-screen">

      {/* -- Top bar -- */}

      <header
        className="flex items-center justify-between px-6 py-4 border-b shrink-0"
        style={{ borderColor: "var(--border-default)" }}
      >
        <BackButton />
        <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Search & Retrieval
        </h1>
        <div className="w-12" />
      </header>


      {/* -- Main content -- */}

      <div className="flex flex-1 flex-col md:flex-row overflow-hidden">

        {/* -- Left column: Content input -- */}

        <div
          className="flex flex-col w-full md:w-1/2 border-b md:border-b-0 md:border-r"
          style={{ borderColor: "var(--border-default)" }}
        >

          {/* Column header */}
          <div
            className="px-6 py-3 border-b flex items-center justify-between shrink-0"
            style={{ borderColor: "var(--border-default)" }}
          >
            <span className="text-xs font-medium uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
              Source Content
            </span>

            <div className="flex items-center gap-2">
              {/* Load sample data pill */}
              {!sampleLoaded && (
                <button
                  onClick={handleLoadSample}
                  className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full border transition-colors duration-200"
                  style={{
                    borderColor: "var(--border-default)",
                    color: "var(--text-secondary)",
                    background: "var(--bg-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-strong)";
                    e.currentTarget.style.background = "var(--bg-tertiary)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-default)";
                    e.currentTarget.style.background = "var(--bg-secondary)";
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Load sample data
                </button>
              )}

              {/* Clear button */}
              {content.length > 0 && !sampleLoaded && (
                <button
                  onClick={handleClear}
                  className="text-xs font-medium px-2 py-0.5 rounded transition-colors duration-200"
                  style={{ color: "var(--text-tertiary)" }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "var(--error)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-tertiary)"; }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>


          {/* Content area */}
          <div className="flex flex-1 flex-col min-h-0">

            {sampleLoaded ? (
              /* -- Sample data loaded view -- */
              <div className="flex flex-1 flex-col">
                <div className="flex-1 overflow-y-auto px-6 py-5 no-scrollbar">

                  {/* Status badge */}
                  <div
                    className="animate-fade-in inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-5"
                    style={{ background: "var(--bg-tertiary)", color: "var(--success)" }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)" }} />
                    Sample data loaded
                  </div>

                  {/* Description */}
                  <p
                    className="animate-fade-in text-sm leading-relaxed mb-5"
                    style={{ color: "var(--text-secondary)", animationDelay: "50ms", opacity: 0 }}
                  >
                    Content from all seven Harry Potter books has been loaded.
                    Use the search panel to find relevant passages.
                  </p>

                  {/* Book list */}
                  <div
                    className="animate-fade-in"
                    style={{ animationDelay: "100ms", opacity: 0 }}
                  >
                    <p
                      className="text-xs font-medium uppercase tracking-wide mb-3"
                      style={{ color: "var(--text-tertiary)" }}
                    >
                      Included books
                    </p>

                    <ul className="flex flex-col gap-2">
                      {HARRY_POTTER_BOOKS.map((book, i) => (
                        <li
                          key={book}
                          className="animate-fade-in flex items-start gap-3 text-sm"
                          style={{
                            color: "var(--text-primary)",
                            animationDelay: `${150 + i * 40}ms`,
                            opacity: 0,
                          }}
                        >
                          <span
                            className="shrink-0 w-5 h-5 rounded-md flex items-center justify-center text-xs font-mono font-medium mt-0.5"
                            style={{ background: "var(--bg-tertiary)", color: "var(--text-tertiary)" }}
                          >
                            {i + 1}
                          </span>
                          {book}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Clear and enter your own */}
                  <button
                    onClick={handleClearSample}
                    className="animate-fade-in mt-6 inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors duration-200"
                    style={{
                      animationDelay: "450ms",
                      opacity: 0,
                      color: "var(--text-inverse)",
                      background: "var(--accent)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "var(--accent-hover)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "var(--accent)";
                    }}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 6 6 18" />
                      <path d="m6 6 12 12" />
                    </svg>
                    Clear &amp; enter your own
                  </button>
                </div>
              </div>
            ) : (
              /* -- Manual text input -- */
              <>
                <textarea
                  value={content}
                  onChange={(e) => handleContentChange(e.target.value)}
                  placeholder="Paste your content here..."
                  className="flex-1 w-full px-6 py-4 text-sm leading-relaxed bg-transparent no-scrollbar"
                  style={{
                    fontFamily: "var(--font-sans)",
                    color: "var(--text-primary)",
                    minHeight: "200px",
                  }}
                />

                {/* Character counter */}
                <div
                  className="px-6 py-2.5 border-t flex items-center justify-end shrink-0"
                  style={{ borderColor: "var(--border-default)" }}
                >
                  <span
                    className="text-xs font-mono font-medium tabular-nums"
                    style={{ color: isOverLimit ? "var(--error)" : "var(--text-tertiary)" }}
                  >
                    {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>


        {/* -- Right column: Search + results -- */}

        <div className="flex flex-col w-full md:w-1/2 min-h-0">

          {/* Search input */}
          <div
            className="px-6 py-3 border-b shrink-0"
            style={{ borderColor: "var(--border-default)" }}
          >
            <div
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl border transition-colors duration-200"
              style={{
                borderColor: "var(--border-default)",
                background: "var(--bg-secondary)",
              }}
            >
              <svg
                width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                style={{ color: "var(--text-tertiary)", flexShrink: 0 }}
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>

              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search content..."
                className="flex-1 bg-transparent text-sm"
                style={{ color: "var(--text-primary)" }}
              />

              {query && (
                <button
                  onClick={() => { setQuery(""); setResults([]); setHasSearched(false); }}
                  className="transition-colors duration-200"
                  style={{ color: "var(--text-tertiary)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6 6 18" />
                    <path d="m6 6 12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>


          {/* Filters */}
          <div
            className="px-6 py-3 border-b flex flex-wrap items-center gap-4 shrink-0"
            style={{ borderColor: "var(--border-default)" }}
          >
            {/* Method filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>
                Method
              </span>
              <div
                className="flex rounded-lg border overflow-hidden"
                style={{ borderColor: "var(--border-default)" }}
              >
                {modes.map((m) => (
                  <button
                    key={m.value}
                    onClick={() => setMode(m.value)}
                    className="px-3 py-1.5 text-xs font-medium transition-colors duration-200"
                    style={{
                      background: mode === m.value ? "var(--accent)" : "transparent",
                      color: mode === m.value ? "var(--text-inverse)" : "var(--text-secondary)",
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Limit filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>
                Results
              </span>
              <div
                className="flex rounded-lg border overflow-hidden"
                style={{ borderColor: "var(--border-default)" }}
              >
                {limits.map((l) => (
                  <button
                    key={l}
                    onClick={() => setLimit(l)}
                    className="px-3 py-1.5 text-xs font-medium transition-colors duration-200"
                    style={{
                      background: limit === l ? "var(--accent)" : "transparent",
                      color: limit === l ? "var(--text-inverse)" : "var(--text-secondary)",
                    }}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>
          </div>


          {/* Results */}
          <div className="flex-1 overflow-y-auto px-6 py-4 no-scrollbar">

            {/* Loading states */}
            {(isIngesting || isSearching) && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                  {isIngesting ? "Indexing content..." : "Searching..."}
                </p>
              </div>
            )}

            {/* Error */}
            {error && !isSearching && !isIngesting && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-sm" style={{ color: "var(--error)" }}>{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-xs font-medium transition-colors duration-200"
                  style={{ color: "var(--text-tertiary)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Empty state */}
            {!hasSearched && !isSearching && !isIngesting && !error && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <svg
                  width="40" height="40" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"
                  style={{ color: "var(--border-strong)" }}
                  className="mb-4"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" />
                </svg>
                <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                  {hasContent
                    ? "Type a query above and press Enter"
                    : "Paste content on the left, then search here"}
                </p>
              </div>
            )}

            {/* No results */}
            {hasSearched && results.length === 0 && !isSearching && !error && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                  No matching results found
                </p>
              </div>
            )}

            {/* Results */}
            {results.length > 0 && !isSearching && (
              <div className="flex flex-col gap-3">
                <p className="text-xs font-medium mb-1" style={{ color: "var(--text-tertiary)" }}>
                  {results.length} result{results.length !== 1 ? "s" : ""} found
                </p>

                {results.map((result, i) => (
                  <div
                    key={result.id}
                    className="animate-fade-in p-4 rounded-xl border transition-colors duration-200"
                    style={{
                      animationDelay: `${i * 50}ms`,
                      opacity: 0,
                      borderColor: "var(--border-default)",
                      background: "var(--bg-secondary)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "var(--bg-tertiary)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "var(--bg-secondary)";
                    }}
                  >
                    <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
                      {result.content}
                    </p>

                    <div className="flex items-center gap-3 mt-3 flex-wrap">
                      <span
                        className="text-xs font-mono px-2 py-0.5 rounded"
                        style={{ background: "var(--bg-tertiary)", color: "var(--text-tertiary)" }}
                      >
                        score: {result.score.toFixed(2)}
                      </span>

                      {/* Show book title for sample data results */}
                      {result.metadata?.book_title && (
                        <span
                          className="text-xs font-medium px-2 py-0.5 rounded"
                          style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}
                        >
                          {result.metadata.book_title}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
