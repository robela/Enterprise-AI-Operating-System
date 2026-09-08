"use client";

import { useState, useCallback } from "react";
import { submitDecisionSurvey } from "../api";
import { toast } from "sonner";

interface UseSurveyProps {
  token: string | null;
}

export function useSurvey({ token }: UseSurveyProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [actionTaken, setActionTaken] = useState<"managed" | "referred" | null>(null);
  const [intentChanged, setIntentChanged] = useState<boolean | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const openSurvey = useCallback(() => {
    setStep(1);
    setActionTaken(null);
    setIntentChanged(null);
    setIsSaving(false);
    setIsOpen(true);
  }, []);

  const closeSurvey = useCallback(() => {
    setIsOpen(false);
  }, []);

  const handleActionTaken = useCallback((value: "managed" | "referred") => {
    setActionTaken(value);
    setStep(2);
  }, []);

  const handleIntentChanged = useCallback(
    (value: boolean, chatId: string | null, onComplete: () => void) => {
      if (!token || !chatId || !actionTaken) return;

      setIntentChanged(value);
      setStep(3);

      // After 2s on summary, show saving message and submit
      setTimeout(async () => {
        setIsSaving(true);
        try {
          await submitDecisionSurvey(
            { chat_id: chatId, action_taken: actionTaken, intent_changed: value },
            token
          );
          // After save, wait 2s then close
          setTimeout(() => {
            setIsOpen(false);
            onComplete();
            toast.success("Survey response saved.");
          }, 2000);
        } catch {
          toast.error("Failed to submit survey. Please try again.");
          setIsSaving(false);
          setStep(2);
        }
      }, 2000);
    },
    [token, actionTaken]
  );

  return {
    isOpen,
    step,
    actionTaken,
    intentChanged,
    isSaving,
    openSurvey,
    closeSurvey,
    handleActionTaken,
    handleIntentChanged,
  } as const;
}
