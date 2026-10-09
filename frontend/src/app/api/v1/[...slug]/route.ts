import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

const DEFAULT_PROXY_TIMEOUT_MS = 120000;

/**
 * Proxy API requests to the backend service
 * This route handles all /api/v1/* requests and forwards them to the backend
 */
export async function GET(req: NextRequest) {
  return proxyRequest(req);
}

export async function POST(req: NextRequest) {
  return proxyRequest(req);
}

export async function PUT(req: NextRequest) {
  return proxyRequest(req);
}

export async function DELETE(req: NextRequest) {
  return proxyRequest(req);
}

export async function PATCH(req: NextRequest) {
  return proxyRequest(req);
}

async function proxyRequest(req: NextRequest) {
  try {
    const backendUrl =
      process.env.BACKEND_URL?.trim() ||
      process.env.NEXT_PUBLIC_BACKEND_URL?.trim();

    if (!backendUrl) {
      console.error('Backend URL not configured');
      return NextResponse.json(
        { error: 'Backend URL not configured' },
        { status: 500 }
      );
    }

    const timeoutMs = Number.parseInt(
      process.env.PROXY_TIMEOUT_MS ?? `${DEFAULT_PROXY_TIMEOUT_MS}`,
      10
    );

    // Extract the path from the URL (everything after /api/v1/)
    const pathname = req.nextUrl.pathname;
    const pathAfterApiV1 = pathname.replace(/^\/api\/v1\//, '');
    const candidateUrls = buildCandidateUrls(backendUrl, pathAfterApiV1, req.nextUrl.search);

    // Prepare headers
    const headers = new Headers();
    req.headers.forEach((value, key) => {
      // Skip host and other headers that shouldn't be forwarded
      if (!['host', 'connection', 'content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    });

    // Forward the request
    const init: RequestInit = {
      method: req.method,
      headers,
    };

    // Include body for non-GET requests.
    // We buffer once so retries can reuse the same payload safely.
    let requestBody: ArrayBuffer | undefined;
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      const bodyBuffer = await req.arrayBuffer();
      if (bodyBuffer.byteLength > 0) {
        requestBody = bodyBuffer;
      }
    }

    const attemptErrors: string[] = [];

    for (const url of candidateUrls) {
      try {
        console.log(`Proxying ${req.method} ${pathname} to ${url.toString()}`);

        const fetchInit: RequestInit = {
          ...init,
          cache: 'no-store',
          signal: AbortSignal.timeout(Number.isFinite(timeoutMs) ? timeoutMs : DEFAULT_PROXY_TIMEOUT_MS),
        };

        if (requestBody && requestBody.byteLength > 0) {
          fetchInit.body = requestBody;
        }

        const response = await fetch(url.toString(), fetchInit);

        // Forward the response
        const newHeaders = new Headers(response.headers);
        newHeaders.set('x-forwarded-by', 'enterprise-ai-frontend');

        return new NextResponse(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: newHeaders,
        });
      } catch (error) {
        const code = getErrorCode(error);
        const message = error instanceof Error ? error.message : String(error);
        const attempt = `${url.toString()} -> ${code}: ${message}`;
        attemptErrors.push(attempt);
        console.error('Proxy attempt failed:', attempt);
      }
    }

    return NextResponse.json(
      {
        error: 'Backend request timed out or was unreachable',
        details: attemptErrors,
      },
      { status: 504 }
    );
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    );
  }
}

function buildCandidateUrls(baseUrl: string, pathAfterApiV1: string, search: string): URL[] {
  const primary = new URL(`/api/v1/${pathAfterApiV1}`, baseUrl);
  primary.search = search;

  const urls: URL[] = [primary];

  // In mixed Windows/WSL local development, localhost and 127.0.0.1 can resolve differently.
  if (primary.hostname === 'localhost') {
    const secondary = new URL(primary.toString());
    secondary.hostname = '127.0.0.1';
    urls.push(secondary);
  } else if (primary.hostname === '127.0.0.1') {
    const secondary = new URL(primary.toString());
    secondary.hostname = 'localhost';
    urls.push(secondary);
  }

  return urls;
}

function getErrorCode(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    const maybeCode = (error as { code?: unknown }).code;
    if (typeof maybeCode === 'string' && maybeCode.length > 0) {
      return maybeCode;
    }

    const maybeCause = (error as { cause?: { code?: unknown } }).cause;
    if (typeof maybeCause?.code === 'string' && maybeCause.code.length > 0) {
      return maybeCause.code;
    }
  }

  return 'UNKNOWN_PROXY_ERROR';
}
