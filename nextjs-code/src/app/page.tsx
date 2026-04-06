"use client";

import Link from "next/link";


const features = [
  {
    title: "Search & Retrieval",
    href: "/search",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    ),
    summary: "See how different retrieval strategies find relevant content from a body of text.",
    steps: [
      "Paste any text (or load the included Harry Potter sample data)",
      "Type a search query and press Enter",
      "Switch between Vector, BM25, and Combined (RRF) retrieval methods",
      "Compare how each method ranks and surfaces different snippets",
      "Adjust the result count (5, 10, or 20) to control output volume",
    ],
    tags: ["Vector Search", "BM25", "Hybrid RRF"],
  },
  {
    title: "Chat Interface",
    href: "/chat",
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    summary: "Ask questions in natural language and get AI-generated answers grounded in retrieved context.",
    steps: [
      "Start a new chat session",
      "Type a question or prompt and press Enter",
      "View the AI response rendered in a clean conversational layout",
      "Continue the conversation with follow-up questions",
      "Start a fresh session anytime with the New Chat button",
    ],
    tags: ["Conversational", "RAG", "Real-time"],
  },
];


export default function Dashboard() {
  return (
    <div className="flex flex-1 flex-col items-center px-6 py-12 sm:py-16">

      {/* -- Header -- */}

      <div className="animate-fade-in max-w-3xl text-center mb-14">
        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium tracking-wide uppercase mb-6"
          style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "var(--success)" }}
          />
          Interactive Demo
        </div>

        <h1
          className="text-4xl sm:text-5xl font-bold tracking-tight leading-tight mb-4"
          style={{ color: "var(--text-primary)" }}
        >
          Retrieval-Augmented Generation
        </h1>

        <p
          className="text-base sm:text-lg leading-relaxed max-w-2xl mx-auto mb-4"
          style={{ color: "var(--text-secondary)" }}
        >
          This project demonstrates how RAG works end-to-end: retrieving relevant
          content from a text corpus using different search strategies, then using
          that context to power AI-generated responses.
        </p>

        <p
          className="text-sm leading-relaxed max-w-xl mx-auto"
          style={{ color: "var(--text-tertiary)" }}
        >
          Pick one of the two modules below to get started. Each one focuses on a
          different part of the RAG pipeline.
        </p>
      </div>


      {/* -- Feature cards -- */}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full max-w-5xl">
        {features.map((feature, i) => (
          <Link
            key={feature.href}
            href={feature.href}
            className="animate-slide-up group relative flex flex-col p-7 sm:p-8 rounded-2xl border transition-all duration-300 hover:-translate-y-1"
            style={{
              animationDelay: `${i * 100 + 200}ms`,
              opacity: 0,
              background: "var(--bg-primary)",
              borderColor: "var(--border-default)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--border-strong)";
              e.currentTarget.style.background = "var(--bg-secondary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-default)";
              e.currentTarget.style.background = "var(--bg-primary)";
            }}
          >
            {/* Icon + Title row */}
            <div className="flex items-center gap-4 mb-4">
              <div
                className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: "var(--bg-tertiary)", color: "var(--text-primary)" }}
              >
                {feature.icon}
              </div>

              <h2
                className="text-lg font-semibold flex items-center gap-2"
                style={{ color: "var(--text-primary)" }}
              >
                {feature.title}
                <svg
                  width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className="opacity-0 -translate-x-1 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0"
                >
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </h2>
            </div>

            {/* Summary */}
            <p
              className="text-sm leading-relaxed mb-4"
              style={{ color: "var(--text-secondary)" }}
            >
              {feature.summary}
            </p>

            {/* How it works */}
            <p
              className="text-xs font-medium uppercase tracking-wide mb-2.5"
              style={{ color: "var(--text-tertiary)" }}
            >
              How to use
            </p>

            <ul className="flex flex-col gap-2 mb-6">
              {feature.steps.map((step, j) => (
                <li
                  key={j}
                  className="flex items-start gap-2.5 text-sm leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  <span
                    className="shrink-0 w-4.5 h-4.5 rounded flex items-center justify-center text-[10px] font-mono font-medium mt-0.5"
                    style={{ background: "var(--bg-tertiary)", color: "var(--text-tertiary)", minWidth: "18px" }}
                  >
                    {j + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ul>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mt-auto pt-2">
              {feature.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs font-medium px-2.5 py-1 rounded-md"
                  style={{
                    background: "var(--bg-tertiary)",
                    color: "var(--text-secondary)",
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>


      {/* -- Footer note -- */}

      <div
        className="animate-fade-in mt-14 max-w-xl text-center text-xs leading-relaxed"
        style={{ color: "var(--text-tertiary)", animationDelay: "500ms", opacity: 0 }}
      >
        <p>
          This is a demo project for educational purposes only. Requests may be
          throttled.{" "}
          <a
            href="https://github.com/reachbhargav/RAGDemo"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 transition-colors duration-200"
            style={{ color: "var(--text-secondary)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
          >
            View source on GitHub
          </a>
        </p>
      </div>
    </div>
  );
}
