"use client";

import React from "react";
import { Message } from "../types";

interface CitationsProps {
  message: Message;
  onDocumentDownload?: (documentId: string, fileName: string, pageNumber?: number) => void;
}

export default function Citations({ message, onDocumentDownload }: CitationsProps) {
  if (!message.response_metadata?.chunks) {
    return null;
  }

  // Group citations by document for cleaner display
  const citationsByDocument = Object.entries(message.response_metadata.chunks).reduce((acc, [, chunk]) => {
    const docId = chunk.document_id;
    if (!acc[docId]) {
      acc[docId] = {
        fileName: chunk.file_name,
        documentId: docId,
        pages: new Set<number>()
      };
    }
    acc[docId].pages.add(chunk.page_num_within_doc);
    return acc;
  }, {} as Record<string, { fileName: string; documentId: string; pages: Set<number> }>);

  const citations = Object.values(citationsByDocument).map(doc => ({
    fileName: doc.fileName,
    documentId: doc.documentId,
    pages: Array.from(doc.pages).sort((a, b) => a - b)
  }));

  if (citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      <h4 className="text-sm font-semibold text-gray-800 mb-2">Source Documents:</h4>
      <ul className="text-sm text-gray-600 space-y-1">
        {citations.map((citation, index) => (
          <li key={index} className="flex items-start">
            <div>
              {onDocumentDownload ? (
                <button
                  onClick={() => onDocumentDownload(citation.documentId, citation.fileName, citation.pages[0])}
                  className="px-2 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-300 font-medium shadow-sm transition-colors duration-150 max-w-[14rem] truncate"
                  title={citation.fileName}
                >
                  {citation.fileName}
                </button>
              ) : (
                <span className="font-medium">{citation.fileName}</span>
              )}
              <span className="text-gray-500 ml-1">
                {citation.pages.length > 1 ? (
                  <>
                    Pages:{" "}
                    {citation.pages.map((page, pageIndex) => (
                      <span key={page}>
                        {onDocumentDownload ? (
                          <button
                            onClick={() => onDocumentDownload(citation.documentId, citation.fileName, page)}
                            className="text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            {page}
                          </button>
                        ) : (
                          page
                        )}
                        {pageIndex < citation.pages.length - 1 && ", "}
                      </span>
                    ))}
                  </>
                ) : (
                  `Page: ${citation.pages[0]}`
                )}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
