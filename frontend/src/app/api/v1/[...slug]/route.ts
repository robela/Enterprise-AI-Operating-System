import { NextRequest, NextResponse } from 'next/server';

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
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    if (!backendUrl) {
      console.error('Backend URL not configured');
      return NextResponse.json(
        { error: 'Backend URL not configured' },
        { status: 500 }
      );
    }

    // Extract the path from the URL (everything after /api/v1/)
    const pathname = req.nextUrl.pathname;
    const pathAfterApiV1 = pathname.replace(/^\/api\/v1\//, '');
    const url = new URL(`/api/v1/${pathAfterApiV1}`, backendUrl);

    // Copy query parameters
    url.search = req.nextUrl.search;

    console.log(`Proxying ${req.method} ${pathname} to ${url.toString()}`);

    // Prepare headers
    const headers = new Headers();
    req.headers.forEach((value, key) => {
      // Skip host and other headers that shouldn't be forwarded
      if (!['host', 'connection'].includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    });

    // Forward the request
    const init: RequestInit = {
      method: req.method,
      headers,
    };

    // Include body for non-GET requests
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      init.body = await req.text();
    }

    const response = await fetch(url.toString(), init);

    // Forward the response
    const newHeaders = new Headers(response.headers);
    newHeaders.set('x-forwarded-by', 'enterprise-ai-frontend');

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: String(error) },
      { status: 500 }
    );
  }
}
