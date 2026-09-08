"use client";

import React, { useEffect, useState, useRef } from "react";
import { X, ChevronLeft, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getPDFFile } from "../../(admin)/documents/api";

interface PDFPreviewSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string | number;
  documentName: string;
  pageNumber?: number;
  token: string | null;
}

export default function PDFPreviewSidebar({
  isOpen,
  onClose,
  documentId,
  documentName,
  pageNumber = 1,
  token,
}: PDFPreviewSidebarProps) {
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentUrlRef = useRef<string | null>(null);
  const pageNumberRef = useRef(pageNumber);

  // Keep pageNumberRef in sync with pageNumber prop
  useEffect(() => {
    pageNumberRef.current = pageNumber;
  }, [pageNumber]);

  // Fetch PDF when documentId changes or sidebar opens
  useEffect(() => {
    const fetchPDF = async () => {
      if (!isOpen || !token || !documentId) return;

      // Clean up previous URL if exists
      if (currentUrlRef.current) {
        URL.revokeObjectURL(currentUrlRef.current);
        currentUrlRef.current = null;
      }

      setLoading(true);
      setError(null);
      setFileUrl(null);

      try {
        let parsedDocumentId: number;
        if (typeof documentId === "string") {
          parsedDocumentId = parseInt(documentId, 10);
          if (Number.isNaN(parsedDocumentId)) {
            setError("Invalid document ID.");
            setLoading(false);
            return;
          }
        } else {
          parsedDocumentId = documentId;
        }
        const blob = await getPDFFile({
          token,
          document_id: parsedDocumentId,
        });
        const url = URL.createObjectURL(blob);
        currentUrlRef.current = url;
        // Append page number to URL for PDF viewer to open at specific page
        setFileUrl(`${url}#page=${pageNumberRef.current}`);
      } catch (err) {
        console.error("Error fetching PDF:", err);
        setError("Failed to load PDF document.");
      } finally {
        setLoading(false);
      }
    };

    fetchPDF();

    // Cleanup function
    return () => {
      if (currentUrlRef.current) {
        URL.revokeObjectURL(currentUrlRef.current);
        currentUrlRef.current = null;
      }
    };
  }, [isOpen, token, documentId]);

  // Update page number in URL when it changes (without refetching)
  useEffect(() => {
    if (currentUrlRef.current && pageNumber && !loading) {
      setFileUrl(`${currentUrlRef.current}#page=${pageNumber}`);
    }
  }, [pageNumber, loading]);

  // Create a unique key for the iframe to force reload when URL changes
  const iframeKey = `${documentId}-${pageNumber}`;

  const handleDownload = () => {
    if (!currentUrlRef.current) return;
    const link = document.createElement("a");
    link.href = currentUrlRef.current;
    link.download = documentName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Mobile/Tablet: Full screen overlay - uses CSS media query */}
      <div className="md:hidden fixed inset-0 z-50 bg-white flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0">
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <div className="flex flex-col min-w-0">
              <h2 className="text-sm font-semibold truncate" title={documentName}>
                {documentName}
              </h2>
              {pageNumber && (
                <span className="text-xs text-gray-500">Page {pageNumber}</span>
              )}
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={handleDownload} title="Download PDF" className="shrink-0">
            <Download className="h-5 w-5" />
          </Button>
        </div>

        {/* PDF Content */}
        <div className="flex-1 overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full text-red-500 p-4">
              {error}
            </div>
          )}
          {fileUrl && !loading && !error && (
            <iframe
              key={iframeKey}
              src={fileUrl}
              title={documentName}
              className="w-full h-full border-0"
            />
          )}
        </div>
      </div>

      {/* Desktop: Push-in sidebar - uses CSS media query */}
      <div className="hidden md:flex w-full h-full flex-col border-l bg-white shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50 shrink-0">
          <div className="flex flex-col min-w-0 flex-1">
            <h2 className="text-sm font-semibold truncate" title={documentName}>
              {documentName}
            </h2>
            {pageNumber && (
              <span className="text-xs text-gray-500">Page {pageNumber}</span>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button variant="ghost" size="icon" onClick={handleDownload} title="Download PDF">
              <Download className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose} title="Close">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* PDF Content */}
        <div className="flex-1 overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full text-red-500 p-4 text-center">
              {error}
            </div>
          )}
          {fileUrl && !loading && !error && (
            <iframe
              key={iframeKey}
              src={fileUrl}
              title={documentName}
              className="w-full h-full border-0"
            />
          )}
        </div>
      </div>
    </>
  );
}
