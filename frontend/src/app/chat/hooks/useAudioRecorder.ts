"use client";

import { useState, useRef, useCallback } from "react";

export type RecordingState = "idle" | "listening" | "processing";

interface UseAudioRecorderReturn {
  state: RecordingState;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  resetState: () => void;
}

export function useAudioRecorder(
  onRecordingComplete: (blob: Blob, contentType: string) => void | Promise<void>
): UseAudioRecorderReturn {
  const [state, setState] = useState<RecordingState>("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const contentType = mediaRecorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: contentType });
        cleanup();

        if (blob.size > 0) {
          setState("processing");
          try {
            await onRecordingComplete(blob, contentType);
          } finally {
            setState("idle");
          }
        } else {
          setState("idle");
        }
      };

      mediaRecorder.onerror = () => {
        cleanup();
        setState("idle");
      };

      mediaRecorder.start();
      setState("listening");
    } catch {
      cleanup();
      setState("idle");
      throw new Error(
        "Microphone access denied. Please allow microphone access in your browser settings."
      );
    }
  }, [cleanup, onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const resetState = useCallback(() => {
    cleanup();
    setState("idle");
  }, [cleanup]);

  return { state, startRecording, stopRecording, resetState };
}
