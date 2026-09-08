"use client";

import React from "react";
import Image from "next/image";
import { ChatImage } from "../types";

interface ImageDisplayProps {
  image: ChatImage;
  isUserImage?: boolean;
  onDocumentDownload?: (documentId: number | string, fileName: string, pageNumber?: number) => void;
}

export default function ImageDisplay({
  image,
  isUserImage = false,
  onDocumentDownload
}: ImageDisplayProps) {
  return (
    <div className="relative group max-w-md" key={image.image_id}>
      <Image
        src={`data:image/jpeg;base64,${image.image_data}`}
        alt={image.caption}
        width={800}
        height={600}
        className="rounded-lg max-w-full h-auto border"
        unoptimized
      />
      <div className="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded">
        {isUserImage ? (
          image.caption
        ) : (
          // For images, show page and document info
          <div>
            <div>{image.caption}</div>
            {image.document_name && image.page_number && (
              <div className="mt-1 text-gray-500">
                From:{" "}
                {onDocumentDownload && image.document_id ? (
                  <button
                    onClick={() => onDocumentDownload(image.document_id!, image.document_name!, image.page_number)}
                    className="text-blue-600 hover:text-blue-800 underline max-w-[14rem] truncate inline"
                  >
                    Page {image.page_number}, {image.document_name}
                  </button>
                ) : (
                  <span>Page {image.page_number}, {image.document_name}</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
