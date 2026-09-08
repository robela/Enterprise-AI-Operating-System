"use client";

import { useState, useCallback } from "react";
import { toast } from "sonner";
import {
  submitDecisionSupport,
  getGroupedTags,
  GroupedTagsOut,
  getPrograms,
} from "../api";

export interface ProgramOption {
  program_id: number | string;
  name: string;
  is_active?: boolean;
}

export interface HewEntry {
  id: string;
  name: string;
  phcuId: string;
  healthPostId: string;
  woreda: string;
  zone: string;
  region: string;
}

export interface HealthPostEntry {
  id: string;
  name: string;
  phcuId: string;
  woreda: string;
  zone: string;
  region: string;
}

export interface PhcuEntry {
  id: string;
  name: string;
}

export interface ContextOptions {
  phcus: PhcuEntry[];
  healthPosts: HealthPostEntry[];
  hews: HewEntry[];
}

export interface DSSelections {
  hew: { id: string; name: string; woreda: string } | null;
  languagePref: string | null;
  actionTaken: "managed" | "referred" | null;
  intentChanged: boolean | null;
  program: { id: number; name: string } | null;
  tag: { id: number; name: string } | null;
}

interface MessageContext {
  chatId: string;
  requestId: number;
  question: string;
  answer: string;
}

interface UseDecisionSupportProps {
  token: string | null;
}

const TOTAL_STEPS = 7;

export function useDecisionSupport({ token }: UseDecisionSupportProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [messageContext, setMessageContext] = useState<MessageContext | null>(null);

  const [contextOptions, setContextOptions] = useState<ContextOptions | null>(null);
  const [programs, setPrograms] = useState<ProgramOption[]>([]);
  const [groupedTags, setGroupedTags] = useState<GroupedTagsOut | null>(null);

  const [selections, setSelections] = useState<DSSelections>({
    hew: null,
    languagePref: null,
    actionTaken: null,
    intentChanged: null,
    program: null,
    tag: null,
  });

  const loadData = useCallback(async () => {
    if (!token) return;
    setIsLoadingData(true);
    try {
      const [contextData, programsData, tagsData] = await Promise.all([
        fetch("/context-options.json").then((r) => r.json()),
        getPrograms(token),
        getGroupedTags(token),
      ]);
      setContextOptions(contextData as ContextOptions);
      setPrograms(
        programsData.programs.filter(
          (p: ProgramOption) => p.is_active ?? true
        )
      );
      setGroupedTags(tagsData);
    } catch {
      toast.error("Failed to load decision support data.");
    } finally {
      setIsLoadingData(false);
    }
  }, [token]);

  const openSheet = useCallback(
    (chatId: string, requestId: number, question: string, answer: string) => {
      setMessageContext({ chatId, requestId, question, answer });
      setStep(1);
      setSelections({
        hew: null,
        languagePref: null,
        actionTaken: null,
        intentChanged: null,
        program: null,
        tag: null,
      });
      setIsOpen(true);
      if (!contextOptions || !groupedTags) {
        loadData();
      }
    },
    [contextOptions, groupedTags, loadData]
  );

  const closeSheet = useCallback(() => {
    if (!isSaving) setIsOpen(false);
  }, [isSaving]);

  const goBack = useCallback(() => setStep((s) => Math.max(1, s - 1)), []);
  const goToStep = useCallback((s: number) => setStep(s), []);

  // Set-only (row clicks) — updates selection without advancing the step
  const setHewOnly = useCallback(
    (hew: { id: string; name: string; woreda: string } | null) =>
      setSelections((prev) => ({ ...prev, hew })),
    []
  );
  const setProgramOnly = useCallback(
    (program: { id: number; name: string } | null) =>
      setSelections((prev) => ({ ...prev, program })),
    []
  );
  const setTagOnly = useCallback(
    (tag: { id: number; name: string } | null) =>
      setSelections((prev) => ({ ...prev, tag })),
    []
  );

  // Skip (clears value and advances)
  const skipHew = useCallback(() => {
    setSelections((prev) => ({ ...prev, hew: null }));
    setStep(2);
  }, []);
  const skipProgram = useCallback(() => {
    setSelections((prev) => ({ ...prev, program: null }));
    setStep(6);
  }, []);
  const skipTag = useCallback(() => {
    setSelections((prev) => ({ ...prev, tag: null }));
    setStep(7);
  }, []);

  // Auto-advance on selection (for single-choice steps)
  const selectLanguage = useCallback((lang: string | null) => {
    setSelections((prev) => ({ ...prev, languagePref: lang }));
    setStep(3);
  }, []);
  const selectActionTaken = useCallback((action: "managed" | "referred") => {
    setSelections((prev) => ({ ...prev, actionTaken: action }));
    setStep(4);
  }, []);
  const selectIntentChanged = useCallback((changed: boolean) => {
    setSelections((prev) => ({ ...prev, intentChanged: changed }));
    setStep(5);
  }, []);

  const handleSubmit = useCallback(
    async (onComplete: () => void) => {
      if (!token || !messageContext || !selections.actionTaken || selections.intentChanged === null)
        return;

      setIsSaving(true);
      try {
        await submitDecisionSupport(
          {
            chat_id: messageContext.chatId,
            request_id: messageContext.requestId,
            question_prompt: messageContext.question,
            ai_answer: messageContext.answer,
            action_taken: selections.actionTaken,
            intent_changed: selections.intentChanged,
            hew: selections.hew?.name ?? null,
            language_preference: selections.languagePref ?? null,
            program: selections.program?.name ?? null,
            tag: selections.tag?.name ?? null,
          },
          token
        );
        toast.success("Decision support saved.");
        setIsOpen(false);
        onComplete();
      } catch {
        toast.error("Failed to save decision support. Please try again.");
      } finally {
        setIsSaving(false);
      }
    },
    [token, messageContext, selections]
  );

  return {
    isOpen,
    step,
    totalSteps: TOTAL_STEPS,
    isSaving,
    isLoadingData,
    selections,
    contextOptions,
    programs,
    groupedTags,
    openSheet,
    closeSheet,
    goBack,
    goToStep,
    setHewOnly,
    setProgramOnly,
    setTagOnly,
    skipHew,
    skipProgram,
    skipTag,
    selectLanguage,
    selectActionTaken,
    selectIntentChanged,
    handleSubmit,
  } as const;
}
