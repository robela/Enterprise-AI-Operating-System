"use client";
import { Button } from "@/components/ui/button";
import React, { ReactNode } from "react";
import { X } from "lucide-react";

type ModalProps = {
  onClose: () => void;
  children: ReactNode;
  maxWidthClass?: string;
};

export default function PopUpModal({ onClose, children, maxWidthClass = "max-w-3xl" }: ModalProps) {
  return (
    <div
      className="fixed inset-0 flex items-center justify-center bg-gray-800 bg-opacity-50 z-50 px-4 sm:px-8"
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-lg shadow-lg ${maxWidthClass} w-full relative`}
        onClick={(e) => e.stopPropagation()}
      >
        <Button
          variant="outline"
          size="icon"
          className="absolute top-4 right-8 z-10"
          onClick={onClose}
        >
          <X className="h-4 w-4" />
        </Button>
        {/* Scrollable Tracer display area */}
        <div className="max-h-[80vh] overflow-y-auto p-4 mt-8">
          {children}
        </div>
      </div>
    </div>
  );
}
