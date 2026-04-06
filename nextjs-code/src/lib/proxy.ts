import { NextRequest, NextResponse } from "next/server";


const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";


/**
 * Proxies a request to the Python backend and returns the response.
 *
 * @param path    - Backend path (e.g. "/api/documents")
 * @param request - Incoming Next.js request (used for method, headers, body)
 * @param init    - Optional fetch overrides (method, body, etc.)
 */
export async function proxy(
  path: string,
  request?: NextRequest,
  init?: RequestInit
): Promise<NextResponse> {
  const url = `${BACKEND_URL}${path}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  try {
    const res = await fetch(url, {
      method: init?.method ?? request?.method ?? "GET",
      headers,
      body: init?.body ?? (request && request.method !== "GET" ? await request.text() : undefined),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });

  } catch {
    return NextResponse.json(
      { error: "Backend unavailable" },
      { status: 502 }
    );
  }
}
