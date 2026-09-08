"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Mic, ArrowUp, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useAudioRecorder } from "../hooks/useAudioRecorder";

export type STTLanguageCode = "am" | "om";

interface MicButtonProps {
  onRecordingComplete: (
    blob: Blob,
    contentType: string,
    language: STTLanguageCode
  ) => void | Promise<void>;
  onListeningChange?: (listening: boolean) => void;
  disabled?: boolean;
  loading?: boolean;
}

const LANGUAGES = [
  { code: "am" as STTLanguageCode, label: "Amharic" },
  { code: "om" as STTLanguageCode, label: "Oromo" },
];

const SESSION_STORAGE_KEY = "stt_language";

function getStoredLanguage(): STTLanguageCode {
  if (typeof window === "undefined") return "am";
  return (sessionStorage.getItem(SESSION_STORAGE_KEY) as STTLanguageCode) || "am";
}

export default function MicButton({
  onRecordingComplete,
  onListeningChange,
  disabled = false,
  loading = false,
}: MicButtonProps) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<STTLanguageCode>(getStoredLanguage);

  const handleRecordingComplete = useCallback(
    (blob: Blob, contentType: string) => {
      return onRecordingComplete(blob, contentType, selectedLanguage);
    },
    [onRecordingComplete, selectedLanguage]
  );

  const { state, startRecording, stopRecording } = useAudioRecorder(handleRecordingComplete);

  useEffect(() => {
    onListeningChange?.(state === "listening");
  }, [state, onListeningChange]);

  const handleLanguageSelect = async (langCode: STTLanguageCode) => {
    setSelectedLanguage(langCode);
    sessionStorage.setItem(SESSION_STORAGE_KEY, langCode);
    setPopoverOpen(false);

    try {
      await startRecording();
    } catch {
      toast.error("Microphone access denied. Please allow microphone access.");
    }
  };

  const handleMicClick = () => {
    if (state === "listening") {
      stopRecording();
      return;
    }

    if (state === "idle") {
      setPopoverOpen(true);
    }
  };

  const isDisabled = disabled || loading || state === "processing";

  if (state === "listening") {
    return (
      <div className="flex items-center gap-1.5 sm:gap-2 h-9 px-2 sm:px-3 rounded-full bg-red-50 border border-red-200">
        <div className="flex items-center gap-[2px] sm:gap-[3px]">
          {[0, 1, 2, 3, 4].map((i) => (
            <span
              key={i}
              className="inline-block w-[2px] sm:w-[3px] rounded-full bg-red-500 animate-bounce"
              style={{
                height: `${6 + Math.random() * 7}px`,
                animationDelay: `${i * 0.12}s`,
                animationDuration: "0.5s",
              }}
            />
          ))}
        </div>
        <span className="hidden sm:inline text-xs text-red-600 font-medium">Recording</span>
        <Button
          type="button"
          variant="destructive"
          size="sm"
          onClick={handleMicClick}
          className="h-7 w-7 p-0 rounded-full"
          aria-label="Send recording"
        >
          <ArrowUp className="h-3.5 w-3.5" />
        </Button>
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
          <TooltipTrigger asChild>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={handleMicClick}
                disabled={isDisabled}
                className="h-9 w-9 rounded-full"
                aria-label="Record voice message"
              >
                {state === "processing" && <Loader2 className="h-4 w-4 animate-spin" />}
                {state === "idle" && <Mic className="h-4 w-4" />}
              </Button>
            </PopoverTrigger>
          </TooltipTrigger>
          <PopoverContent className="w-32 p-1" align="start">
            {LANGUAGES.map((lang) => (
              <Button
                key={lang.code}
                variant="ghost"
                size="sm"
                className="w-full justify-start"
                onClick={() => handleLanguageSelect(lang.code)}
              >
                {lang.label}
              </Button>
            ))}
          </PopoverContent>
        </Popover>
        <TooltipContent>Voice input</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
