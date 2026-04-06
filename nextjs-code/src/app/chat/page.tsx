"use client";

import Link from "next/link";
import { useState, useRef, useEffect, useCallback } from "react";
import { MAX_CHARS, HARRY_POTTER_BOOKS } from "@/lib/sample-data";
import {
  ingestDocument,
  deleteDocument,
  createChat,
  sendChatMessage,
  checkChatStatus,
} from "@/lib/api";


type ChatState = "landing" | "setup" | "active";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}


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


export default function ChatPage() {
  const [chatState, setChatState] = useState<ChatState>("landing");
  const [content, setContent] = useState("");
  const [sampleLoaded, setSampleLoaded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatEnabled, setChatEnabled] = useState<boolean | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const docIdRef = useRef<string | null>(null);
  const chatIdRef = useRef<string | null>(null);

  const charCount = content.length;
  const isOverLimit = charCount > MAX_CHARS;
  const hasContent = content.trim().length > 0 || sampleLoaded;


  /* -- Check chat status on mount -- */

  useEffect(() => {
    checkChatStatus().then(setChatEnabled);
  }, []);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);


  /* -- State transitions -- */

  const handleNewChat = () => {
    setChatState("setup");
    setContent("");
    setSampleLoaded(false);
    setMessages([]);
    setInput("");
    setIsTyping(false);
    setError(null);
  };

  const handleLoadSample = () => {
    setSampleLoaded(true);
    setContent("");
    setError(null);
  };

  const handleClearSample = () => {
    setSampleLoaded(false);
    setContent("");
    setError(null);
  };


  /**
   * Start chatting: ingest custom text if needed, then create a scoped chat session.
   */
  const handleStartChatting = async () => {
    setError(null);
    setIsLoading(true);

    try {
      let scope: { doc_id: string } | { source: string };

      if (sampleLoaded) {
        scope = { source: "sample" };
      } else {
        // Ingest custom text first
        const { doc_id } = await ingestDocument("Custom Content", content);
        docIdRef.current = doc_id;
        scope = { doc_id };
      }

      // Create scoped chat
      const chatId = await createChat(scope);
      chatIdRef.current = chatId;

      setChatState("active");
      setTimeout(() => inputRef.current?.focus(), 100);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start chat");
    } finally {
      setIsLoading(false);
    }
  };


  /**
   * Reset everything: clean up backend resources, return to landing.
   */
  const handleReset = async () => {
    // Clean up custom doc (also deletes associated chat server-side)
    if (docIdRef.current) {
      deleteDocument(docIdRef.current);
      docIdRef.current = null;
    }
    chatIdRef.current = null;

    setChatState("landing");
    setContent("");
    setSampleLoaded(false);
    setMessages([]);
    setInput("");
    setIsTyping(false);
    setError(null);
  };


  /* -- Messaging -- */

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isTyping || !chatIdRef.current) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);
    setError(null);

    try {
      const data = await sendChatMessage(chatIdRef.current, trimmed);

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
      };

      setMessages((prev) => [...prev, aiMsg]);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get response");
    } finally {
      setIsTyping(false);
    }
  }, [input, isTyping]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };


  /* -- Content label for the header badge -- */

  const contentLabel = sampleLoaded
    ? "Sample data"
    : `Custom content · ${charCount.toLocaleString()} chars`;


  return (
    <div className="flex flex-1 flex-col h-screen">

      {/* -- Top bar -- */}

      <header
        className="flex items-center justify-between px-6 py-4 border-b shrink-0"
        style={{ borderColor: "var(--border-default)" }}
      >
        <BackButton />

        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Chat
          </h1>

          {/* Content badge — visible in active chat state */}
          {chatState === "active" && (
            <span
              className="animate-fade-in inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
              style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)" }} />
              {contentLabel}
            </span>
          )}
        </div>

        {chatState === "active" ? (
          <button
            onClick={handleReset}
            className="text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors duration-200"
            style={{
              borderColor: "var(--border-default)",
              color: "var(--text-secondary)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--border-strong)";
              e.currentTarget.style.color = "var(--text-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-default)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            New Chat
          </button>
        ) : (
          <div className="w-16" />
        )}
      </header>


      {/* ============================================ */}
      {/* -- LANDING STATE -- */}
      {/* ============================================ */}

      {chatState === "landing" && (
        <div className="flex flex-1 flex-col items-center justify-center px-6">
          <div className="animate-scale-in flex flex-col items-center text-center max-w-md">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: "var(--bg-tertiary)" }}
            >
              <svg
                width="28" height="28" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                style={{ color: "var(--text-secondary)" }}
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>

            <h2
              className="text-2xl font-semibold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Start a conversation
            </h2>

            <p
              className="text-sm leading-relaxed mb-8"
              style={{ color: "var(--text-secondary)" }}
            >
              Provide your content, then ask questions and get AI-powered
              responses using retrieval-augmented generation.
            </p>

            {/* Chat disabled warning */}
            {chatEnabled === false && (
              <p
                className="text-xs leading-relaxed mb-6 px-4 py-2.5 rounded-xl"
                style={{ background: "var(--bg-tertiary)", color: "var(--warning)" }}
              >
                Chat is currently unavailable — LLM API key is not configured on the server.
              </p>
            )}

            <button
              onClick={handleNewChat}
              disabled={chatEnabled === false}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
              style={{
                background: "var(--accent)",
                color: "var(--text-inverse)",
              }}
              onMouseEnter={(e) => {
                if (chatEnabled !== false) e.currentTarget.style.background = "var(--accent-hover)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "var(--accent)";
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14" />
                <path d="M5 12h14" />
              </svg>
              New Chat
            </button>
          </div>
        </div>
      )}


      {/* ============================================ */}
      {/* -- CONTENT SETUP STATE -- */}
      {/* ============================================ */}

      {chatState === "setup" && (
        <div className="flex flex-1 flex-col items-center overflow-y-auto no-scrollbar px-6 py-10">
          <div className="animate-fade-in w-full max-w-2xl">

            {/* Title */}
            <h2
              className="text-xl font-semibold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Add your content
            </h2>
            <p
              className="text-sm leading-relaxed mb-6"
              style={{ color: "var(--text-secondary)" }}
            >
              Paste the text you want to chat about, or load the sample dataset to try it out.
              The AI will use this content as context when answering your questions.
            </p>


            {sampleLoaded ? (
              /* -- Sample data loaded -- */
              <div
                className="animate-fade-in rounded-2xl border p-6"
                style={{ borderColor: "var(--border-default)", background: "var(--bg-secondary)" }}
              >
                {/* Status badge */}
                <div
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-5"
                  style={{ background: "var(--bg-tertiary)", color: "var(--success)" }}
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--success)" }} />
                  Sample data loaded
                </div>

                <p
                  className="text-sm leading-relaxed mb-5"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Content from all seven Harry Potter books has been loaded.
                  You can now start chatting to ask questions about the series.
                </p>

                {/* Book list */}
                <p
                  className="text-xs font-medium uppercase tracking-wide mb-3"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  Included books
                </p>

                <ul className="flex flex-col gap-2 mb-6">
                  {HARRY_POTTER_BOOKS.map((book, i) => (
                    <li
                      key={book}
                      className="animate-fade-in flex items-start gap-3 text-sm"
                      style={{
                        color: "var(--text-primary)",
                        animationDelay: `${100 + i * 40}ms`,
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

                <button
                  onClick={handleClearSample}
                  className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors duration-200"
                  style={{
                    color: "var(--text-inverse)",
                    background: "var(--accent)",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--accent-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "var(--accent)")}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6 6 18" />
                    <path d="m6 6 12 12" />
                  </svg>
                  Clear &amp; enter your own
                </button>
              </div>

            ) : (
              /* -- Manual text input -- */
              <div>
                {/* Load sample pill */}
                <div className="flex items-center gap-3 mb-4">
                  <button
                    onClick={handleLoadSample}
                    className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border transition-colors duration-200"
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

                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                    or paste your own below
                  </span>
                </div>

                {/* Textarea */}
                <div
                  className="rounded-2xl border overflow-hidden"
                  style={{ borderColor: "var(--border-default)", background: "var(--bg-secondary)" }}
                >
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Paste your content here..."
                    className="w-full px-5 py-4 text-sm leading-relaxed bg-transparent no-scrollbar"
                    style={{
                      fontFamily: "var(--font-sans)",
                      color: "var(--text-primary)",
                      minHeight: "240px",
                    }}
                  />

                  <div
                    className="px-5 py-2.5 border-t flex items-center justify-between"
                    style={{ borderColor: "var(--border-default)" }}
                  >
                    {content.length > 0 && (
                      <button
                        onClick={() => setContent("")}
                        className="text-xs font-medium transition-colors duration-200"
                        style={{ color: "var(--text-tertiary)" }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = "var(--error)")}
                        onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
                      >
                        Clear
                      </button>
                    )}
                    <span
                      className="text-xs font-mono font-medium tabular-nums ml-auto"
                      style={{ color: isOverLimit ? "var(--error)" : "var(--text-tertiary)" }}
                    >
                      {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            )}


            {/* Error */}
            {error && (
              <p className="mt-4 text-xs" style={{ color: "var(--error)" }}>{error}</p>
            )}

            {/* Start chatting button */}
            <div className="mt-8 flex items-center gap-4">
              <button
                onClick={handleStartChatting}
                disabled={!hasContent || isLoading}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  background: "var(--accent)",
                  color: "var(--text-inverse)",
                }}
                onMouseEnter={(e) => {
                  if (hasContent && !isLoading) e.currentTarget.style.background = "var(--accent-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--accent)";
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                {isLoading ? "Setting up..." : "Start chatting"}
              </button>

              {!hasContent && (
                <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                  Add content above to continue
                </span>
              )}
            </div>

            {/* Back to landing */}
            <button
              onClick={handleReset}
              className="mt-4 text-xs font-medium transition-colors duration-200"
              style={{ color: "var(--text-tertiary)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
            >
              Cancel
            </button>
          </div>
        </div>
      )}


      {/* ============================================ */}
      {/* -- ACTIVE CHAT STATE -- */}
      {/* ============================================ */}

      {chatState === "active" && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto no-scrollbar">
            {messages.length === 0 && !isTyping && (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                  Send a message to begin
                </p>
              </div>
            )}

            <div className="max-w-3xl mx-auto px-6 py-6 flex flex-col gap-6">
              {messages.map((msg, i) => (
                <div
                  key={msg.id}
                  className={`animate-fade-in flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  style={{ animationDelay: `${i * 30}ms`, opacity: 0 }}
                >
                  {msg.role === "user" ? (
                    <div
                      className="max-w-[80%] sm:max-w-[70%] px-4 py-3 rounded-2xl rounded-br-md text-sm leading-relaxed"
                      style={{
                        background: "var(--accent)",
                        color: "var(--text-inverse)",
                      }}
                    >
                      {msg.content}
                    </div>
                  ) : (
                    <div className="w-full">
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-6 h-6 rounded-lg flex items-center justify-center"
                          style={{ background: "var(--bg-tertiary)" }}
                        >
                          <svg
                            width="12" height="12" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                            style={{ color: "var(--text-secondary)" }}
                          >
                            <path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z" />
                          </svg>
                        </div>
                        <span
                          className="text-xs font-medium"
                          style={{ color: "var(--text-tertiary)" }}
                        >
                          Assistant
                        </span>
                      </div>

                      <div
                        className="text-sm leading-relaxed whitespace-pre-wrap"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {msg.content}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <div className="animate-fade-in flex justify-start">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center"
                      style={{ background: "var(--bg-tertiary)" }}
                    >
                      <svg
                        width="12" height="12" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        <path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z" />
                      </svg>
                    </div>
                    <div className="flex gap-1">
                      {[0, 1, 2].map((dot) => (
                        <span
                          key={dot}
                          className="w-1.5 h-1.5 rounded-full"
                          style={{
                            background: "var(--text-tertiary)",
                            animation: `fadeIn 1s ease-in-out ${dot * 0.2}s infinite alternate`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Error in chat */}
              {error && !isTyping && (
                <div className="flex justify-start">
                  <p className="text-xs px-3 py-2 rounded-lg" style={{ background: "var(--bg-tertiary)", color: "var(--error)" }}>
                    {error}
                  </p>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>


          {/* Input bar */}
          <div
            className="border-t px-4 sm:px-6 py-4 shrink-0"
            style={{ borderColor: "var(--border-default)" }}
          >
            <div className="max-w-3xl mx-auto">
              <div
                className="flex items-end gap-3 px-4 py-3 rounded-2xl border transition-colors duration-200"
                style={{
                  borderColor: "var(--border-default)",
                  background: "var(--bg-secondary)",
                }}
              >
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    e.target.style.height = "auto";
                    e.target.style.height = Math.min(e.target.scrollHeight, 150) + "px";
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message..."
                  rows={1}
                  className="flex-1 bg-transparent text-sm leading-relaxed"
                  style={{
                    color: "var(--text-primary)",
                    maxHeight: "150px",
                  }}
                />

                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isTyping}
                  className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 disabled:opacity-30"
                  style={{
                    background: input.trim() && !isTyping ? "var(--accent)" : "var(--bg-tertiary)",
                    color: input.trim() && !isTyping ? "var(--text-inverse)" : "var(--text-tertiary)",
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14" />
                    <path d="m12 5 7 7-7 7" />
                  </svg>
                </button>
              </div>

              <p
                className="text-center text-xs mt-2"
                style={{ color: "var(--text-tertiary)" }}
              >
                Press Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
