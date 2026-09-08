"use client";

import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Settings, RotateCcw, Square, ArrowUp } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import MicButton, { STTLanguageCode } from "./MicButton";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancelGeneration?: () => void;
  onToggleSettings?: () => void;
  onClearChat?: () => void;
  onRecordingComplete?: (
    blob: Blob,
    contentType: string,
    language: STTLanguageCode
  ) => void | Promise<void>;
  disabled?: boolean;
  loading?: boolean;
  sttEnabled?: boolean;
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  onCancelGeneration,
  onToggleSettings,
  onClearChat,
  onRecordingComplete,
  disabled = false,
  loading = false,
  sttEnabled = true,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [value]);

  const submitIfReady = () => {
    if (!disabled && !loading && value.trim()) {
      onSubmit();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitIfReady();
    }
  };

  return (
    <footer className="sticky bottom-0 left-0 bg-background space-y-2">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submitIfReady();
        }}
      >
        <div className="rounded-3xl bg-card border px-3 py-2 sm:px-4 sm:py-3 focus-within:ring-1 focus-within:ring-ring transition-colors">
          <Textarea
            ref={textareaRef}
            placeholder="Type your message here..."
            aria-label="Type your message"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || loading}
            rows={1}
            className="min-h-[36px] max-h-[160px] resize-none border-0 bg-transparent shadow-none px-1 py-1 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm"
          />
          <div className="flex items-center justify-between mt-1 sm:mt-2 gap-2">
            <TooltipProvider delayDuration={300}>
              <div className="flex items-center gap-0.5 sm:gap-1 flex-wrap">
                {!isRecording && onToggleSettings && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={onToggleSettings}
                        disabled={disabled || loading}
                        className="h-9 w-9 rounded-full"
                        aria-label="Settings"
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Settings</TooltipContent>
                  </Tooltip>
                )}
                {onRecordingComplete && sttEnabled !== false && (
                  <MicButton
                    onRecordingComplete={onRecordingComplete}
                    onListeningChange={setIsRecording}
                    disabled={disabled}
                    loading={loading}
                  />
                )}
                {!isRecording && onClearChat && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={onClearChat}
                        disabled={disabled || loading}
                        className="h-9 w-9 rounded-full"
                        aria-label="Clear chat"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Clear chat</TooltipContent>
                  </Tooltip>
                )}
              </div>
            </TooltipProvider>
            {loading && onCancelGeneration ? (
              <Button
                type="button"
                size="icon"
                onClick={onCancelGeneration}
                className="h-10 w-10 sm:h-11 sm:w-11 aspect-square rounded-full bg-black text-white ring-1 ring-black/20 shadow-sm hover:bg-black/90 hover:shadow-md active:scale-95 transition-all flex-shrink-0"
                style={{ borderRadius: "9999px" }}
                aria-label="Stop generating"
              >
                <Square className="h-4.5 w-4.5 fill-current" />
              </Button>
            ) : (
              <Button
                type="submit"
                size="icon"
                disabled={disabled || loading || !value.trim()}
                className="h-10 w-10 sm:h-11 sm:w-11 aspect-square rounded-full bg-black text-white ring-1 ring-black/20 shadow-sm hover:bg-black/90 hover:shadow-md active:scale-95 transition-all disabled:bg-black/40 disabled:text-white/90 disabled:shadow-none disabled:scale-100 flex-shrink-0"
                style={{ borderRadius: "9999px" }}
                aria-label="Send message"
              >
                <ArrowUp className="block h-5 w-5 sm:h-5.5 sm:w-5.5 stroke-[2.4]" />
              </Button>
            )}
          </div>
        </div>
        <div className="w-full mt-2 text-center text-xs px-2">
          <strong className="text-yellow-700 bg-yellow-100 px-2 py-1 rounded font-bold">⚠ Trust Warning:</strong> <span className="text-muted-foreground">The answers you receive from Enterprise AI
          must be verified against the source documents.</span>
        </div>
      </form>
    </footer>
  );
}
