import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy API requests to the backend service
 * This route handles all /api/v1/* requests and forwards them to the backend
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string[] }> }
) {
  return proxyRequest(req, params);
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string[] }> }
) {
  return proxyRequest(req, params);
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string[] }> }
) {
  return proxyRequest(req, params);
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string[] }> }
) {
  return proxyRequest(req, params);
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string[] }> }
) {
  return proxyRequest(req, params);
}

async function proxyRequest(
  req: NextRequest,
  params: Promise<{ slug: string[] }>
) {
  try {
    const { slug } = await params;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    if (!backendUrl) {
      return NextResponse.json(
        { error: 'Backend URL not configured' },
        { status: 500 }
      );
    }

    // Reconstruct the path
    const path = slug.join('/');
    const url = new URL(`/api/v1/${path}`, backendUrl);

    // Copy query parameters
    url.search = req.nextUrl.search;

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
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
