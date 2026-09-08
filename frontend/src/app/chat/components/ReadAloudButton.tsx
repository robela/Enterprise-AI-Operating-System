"use client";

import React, { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Volume2, Square, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { synthesizeSpeech } from "../api";

type PlayState = "idle" | "loading" | "playing";

const TTS_SUPPORTED_LANGUAGES = new Set(["am", "om"]);

interface ReadAloudButtonProps {
  responseId: number;
  token: string;
  language?: string;
}

export default function ReadAloudButton({ responseId, token, language }: ReadAloudButtonProps) {
  const isSupported = language ? TTS_SUPPORTED_LANGUAGES.has(language) : false;
  const [state, setState] = useState<PlayState>("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);

  const cleanup = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  };

  const handleClick = async () => {
    if (state === "playing") {
      cleanup();
      setState("idle");
      return;
    }

    setState("loading");

    try {
      const blob = await synthesizeSpeech(responseId, token);
      const url = URL.createObjectURL(blob);

      const audio = new Audio(url);
      audioRef.current = audio;
      urlRef.current = url;

      audio.onended = () => {
        cleanup();
        setState("idle");
      };

      await audio.play();
      setState("playing");
    } catch (error: unknown) {
      cleanup();
      setState("idle");
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 400) {
        toast.error("This language is not supported for audio playback.");
      } else if (status === 404) {
        toast.error("Chat response not found.");
      } else {
        toast.error("Audio service is temporarily unavailable. Please try again later.");
      }
    }
  };

  if (!isSupported) {
    return null;
  }

  return (
    <Button
      size="sm"
      variant="outline"
      className=""
      onClick={handleClick}
    >
      {state === "loading" && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
      {state === "idle" && <Volume2 className="mr-1 h-3 w-3" />}
      {state === "playing" && <Square className="mr-1 h-3 w-3" />}
      {state === "loading" ? "Generating…" : state === "playing" ? "Stop" : "Listen"}
    </Button>
  );
}
