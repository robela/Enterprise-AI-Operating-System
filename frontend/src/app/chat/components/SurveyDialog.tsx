"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CheckCircle2, Loader2 } from "lucide-react";

interface SurveyDialogProps {
  isOpen: boolean;
  step: 1 | 2 | 3;
  actionTaken: "managed" | "referred" | null;
  intentChanged: boolean | null;
  isSaving: boolean;
  onActionTaken: (value: "managed" | "referred") => void;
  onIntentChanged: (value: boolean) => void;
  onClose: () => void;
}

export default function SurveyDialog({
  isOpen,
  step,
  actionTaken,
  intentChanged,
  isSaving,
  onActionTaken,
  onIntentChanged,
  onClose,
}: SurveyDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !isSaving && onClose()}>
      <DialogContent className="w-[calc(100%-2rem)] sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-base">End Chat Survey</DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-4 pt-1">
            <p className="text-sm font-medium text-gray-700">
              Following this consultation, what is your final decision?
            </p>
            <div className="flex flex-wrap gap-2 ">
              <button
                onClick={() => onActionTaken("managed")}
                className="flex-1 min-w-[100px] rounded-xl border-2 border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 transition-all hover:border-gray-900 hover:bg-gray-50 active:scale-95"
              >
                Managed
              </button>
              <button
                onClick={() => onActionTaken("referred")}
                className="flex-1 min-w-[100px] rounded-xl border-2 border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 transition-all hover:border-gray-900 hover:bg-gray-50 active:scale-95"
              >
                Referred
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4 pt-1">
            <p className="text-sm font-medium text-gray-700">
              Did this consultation change your initial intent?
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => onIntentChanged(true)}
                className="flex-1 min-w-[100px] rounded-xl border-2 border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 transition-all hover:border-gray-900 hover:bg-gray-50 active:scale-95"
              >
                Yes
              </button>
              <button
                onClick={() => onIntentChanged(false)}
                className="flex-1 min-w-[100px] rounded-xl border-2 border-gray-200 px-3 py-2 text-xs font-medium text-gray-700 transition-all hover:border-gray-900 hover:bg-gray-50 active:scale-95"
              >
                No
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-5 pt-1">
            <div className="space-y-3">
              <div className="rounded-xl bg-gray-50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wide text-gray-400 font-medium">Action Taken</span>
                  <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600 capitalize">
                    {actionTaken}
                  </span>
                </div>
                <div className="h-px bg-gray-200" />
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wide text-gray-400 font-medium">Intent Changed</span>
                  <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">
                    {intentChanged ? "Yes" : "No"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Saving survey response...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span>Reviewing your responses...</span>
                </>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
