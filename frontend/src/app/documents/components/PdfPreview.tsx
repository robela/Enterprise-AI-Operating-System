"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

type PdfDocument = {
  numPages: number;
  getPage: (pageNumber: number) => Promise<{
    getViewport: (options: { scale: number }) => { width: number; height: number };
    render: (context: { canvasContext: CanvasRenderingContext2D; viewport: { width: number; height: number } }) => { promise: Promise<void> };
  }>;
  destroy: () => Promise<void>;
};

type PdfJs = {
  GlobalWorkerOptions: { workerSrc: string };
  getDocument: (source: { data: ArrayBuffer }) => { promise: Promise<PdfDocument> };
};

declare global {
  interface Window {
    pdfjsLib?: PdfJs;
  }
}

const PDF_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
const PDF_WORKER_URL = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

function loadPdfJs(): Promise<PdfJs> {
  if (window.pdfjsLib) return Promise.resolve(window.pdfjsLib);

  return new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => {
      script?.remove();
      reject(new Error("Timed out loading PDF renderer"));
    }, 12000);
    let script: HTMLScriptElement | null = null;
    const finish = (error?: Error) => {
      window.clearTimeout(timeout);
      if (error) {
        reject(error);
      } else if (window.pdfjsLib) {
        resolve(window.pdfjsLib);
      } else {
        reject(new Error("PDF renderer unavailable"));
      }
    };
    const existingScript = document.querySelector<HTMLScriptElement>('script[data-pdfjs="true"]');
    if (existingScript) {
      script = existingScript;
      existingScript.addEventListener("load", () => finish(), { once: true });
      existingScript.addEventListener("error", () => finish(new Error("Unable to load PDF renderer")), { once: true });
      return;
    }

    script = document.createElement("script");
    script.src = PDF_JS_URL;
    script.async = true;
    script.dataset.pdfjs = "true";
    script.onload = () => finish();
    script.onerror = () => finish(new Error("Unable to load PDF renderer"));
    document.head.appendChild(script);
  });
}

export function PdfPreview({ file }: { file: Blob }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [pdfDocument, setPdfDocument] = useState<PdfDocument | null>(null);
  const [pageCount, setPageCount] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const isDocumentLoaded = pdfDocument !== null;

  useEffect(() => {
    let cancelled = false;
    let loadedDocument: PdfDocument | null = null;
    setPdfDocument(null);
    setPageCount(0);
    setPageNumber(1);
    setError(null);

    void (async () => {
      try {
        const pdfjs = await loadPdfJs();
        pdfjs.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;
        loadedDocument = await pdfjs.getDocument({ data: await file.arrayBuffer() }).promise;
        if (cancelled) {
          await loadedDocument.destroy();
          return;
        }
        setPageCount(loadedDocument.numPages);
        setPdfDocument(loadedDocument);
      } catch {
        if (!cancelled) setError("Unable to render this PDF.");
      }
    })();

    return () => {
      cancelled = true;
      void loadedDocument?.destroy();
    };
  }, [file, reloadKey]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!pdfDocument || !canvas) return;
    let cancelled = false;

    void (async () => {
      try {
        const page = await pdfDocument.getPage(pageNumber);
        if (cancelled) return;
        const viewport = page.getViewport({ scale: 1.4 });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const context = canvas.getContext("2d");
        if (context) await page.render({ canvasContext: context, viewport }).promise;
      } catch {
        if (!cancelled) setError("Unable to render this PDF page.");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [pageNumber, pdfDocument]);

  if (error) {
    return <div className="flex h-full flex-col items-center justify-center gap-3 p-4 text-center text-sm text-destructive"><p>{error}</p><Button type="button" size="sm" variant="outline" onClick={() => setReloadKey((key) => key + 1)}>Retry PDF preview</Button></div>;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 overflow-auto bg-slate-100 p-3 sm:p-5">
        {!isDocumentLoaded && <div className="p-4 text-center text-sm text-muted-foreground">Loading PDF...</div>}
        <canvas ref={canvasRef} className="mx-auto block max-w-full bg-white shadow-sm" />
      </div>
      {isDocumentLoaded && (
        <div className="flex shrink-0 items-center justify-center gap-3 border-t bg-white px-3 py-2 text-sm">
          <Button type="button" size="icon" variant="outline" aria-label="Previous page" disabled={pageNumber <= 1} onClick={() => setPageNumber((page) => Math.max(1, page - 1))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="tabular-nums text-muted-foreground">Page {pageNumber} of {pageCount}</span>
          <Button type="button" size="icon" variant="outline" aria-label="Next page" disabled={pageNumber >= pageCount} onClick={() => setPageNumber((page) => Math.min(pageCount, page + 1))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
