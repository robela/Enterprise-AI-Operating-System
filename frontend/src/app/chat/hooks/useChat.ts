"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Message, TracerData } from "../types";
import { getChatResponse, transcribeAudio, getChatHistory } from "../api";
import { toast } from "sonner";

interface UseChatProps {
  token: string | null;
  userId: string | number | null;
  isAdmin: boolean;
}

interface SendSettings {
  useReference: boolean;
  documentModuleId: string;
  documentProgramId: string;
  sector?: string | null;
}

export function useChat({ token, userId, isAdmin }: UseChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState<string | null>(null);
  const [showTraceModal, setShowTraceModal] = useState(false);
  const [selectedTraceData, setSelectedTraceData] = useState<TracerData>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;

    if (lastMessage.sender === "user") {
      scrollToBottom();
    } else if (lastMessage.sender === "ai") {
      // Small timeout to ensure DOM is ready
      setTimeout(() => {
        const element = document.getElementById(`message-${lastMessage.id}`);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    }
  }, [messages]);

  useEffect(() => {
    if (loading) {
      scrollToBottom();
    }
  }, [loading]);

  const initializeChat = () => {
    setMessages([]);
  };

  useEffect(() => {
    initializeChat();
  }, []);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const clearChat = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    initializeChat();
    setChatId(null);
    setLoading(false);
    toast.success("Starting a fresh conversation.");
  };

  const cancelGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  };

  const resolveDocFilters = (settings: SendSettings) => {
    const moduleId = settings.documentModuleId === "All modules"
      ? null
      : parseInt(settings.documentModuleId);

    const programId = settings.documentProgramId === "All programs"
      ? null
      : parseInt(settings.documentProgramId);

    return { moduleId, programId };
  };

  const sendText = async (text: string, settings: SendSettings) => {
    if (!text.trim() || !token || !userId || loading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      text,
      sender: "user",
      chat_id: chatId,
      tracer_json: {},
      request_id: 0,
      response_metadata: { chunks: {} },
      images: [],
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const { moduleId, programId } = resolveDocFilters(settings);

      const response = await getChatResponse({
        token,
        chat_id: chatId,
        user_id: userId,
        message: text,
        sector: settings.sector ?? null,
        document_modules: moduleId ? [moduleId] : null,
        document_programs: programId ? [programId] : null,
        signal: controller.signal,
        trace: isAdmin,
      });

      setChatId(response.chat_id);
      setMessages((prevMessages) => [
        ...prevMessages,
        { ...response, sender: response.sender, timestamp: new Date() },
      ]);
    } catch (error) {
      if (axios.isCancel(error)) {
        return;
      }
      console.error("Error sending message:", error);
      toast.error("Failed to send message. Please try again.");
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
        setLoading(false);
      }
    }
  };

  const handleSendMessage = async (
    useReference: boolean,
    documentModuleId: string,
    documentProgramId: string,
    sector: string | null = null
  ) => {
    const text = newMessage;
    if (!text.trim() || !token || !userId || loading) return;
    setNewMessage("");
    await sendText(text, { useReference, documentModuleId, documentProgramId, sector });
  };

  const editAndResend = async (
    messageId: number,
    newText: string,
    useReference: boolean,
    documentModuleId: string,
    documentProgramId: string,
    sector: string | null = null
  ) => {
    if (!newText.trim()) return;

    abortControllerRef.current?.abort();

    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === messageId);
      return idx >= 0 ? prev.slice(0, idx) : prev;
    });

    await sendText(newText, { useReference, documentModuleId, documentProgramId, sector });
  };

  const handleTranscribeAudio = async (
    blob: Blob,
    contentType: string,
    languageCode: "am" | "om"
  ): Promise<string | null> => {
    if (!token || loading) return null;

    try {
      const { transcript } = await transcribeAudio({
        file: blob,
        contentType,
        languageCode,
        token,
      });
      return transcript;
    } catch (error) {
      console.error("Error transcribing audio:", error);
      toast.error("Failed to transcribe audio. Please try again.");
      return null;
    }
  };

  const handleShowTrace = (tracerJson: TracerData) => {
    setSelectedTraceData(tracerJson);
    setShowTraceModal(true);
  };

  const loadChatHistory = async (historyChat_id: string) => {
    if (!token) {
      toast.error("Authentication required to load chat history");
      return;
    }

    if (chatId === historyChat_id) {
      return;
    }

    const controller = new AbortController();

    try {
      abortControllerRef.current?.abort();
      abortControllerRef.current = controller;

      // Clear current draft and visible messages immediately when switching
      // to a different conversation so old content is not shown.
      setNewMessage("");
      setMessages([]);
      setChatId(historyChat_id);
      setLoading(true);

      const history = await getChatHistory(historyChat_id, token, controller.signal);

      // Ignore stale responses from superseded requests.
      if (abortControllerRef.current !== controller) {
        return;
      }

      setMessages(history);
    } catch (error) {
      if (axios.isCancel(error)) {
        return;
      }
      console.error("Error loading chat history:", error);
      toast.error("Failed to load conversation history");
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
        setLoading(false);
      }
    }
  };

  return {
    messages,
    setMessages,
    newMessage,
    setNewMessage,
    loading,
    chatId,
    showTraceModal,
    setShowTraceModal,
    selectedTraceData,
    messagesEndRef,
    clearChat,
    cancelGeneration,
    handleSendMessage,
    handleTranscribeAudio,
    editAndResend,
    handleShowTrace,
    loadChatHistory,
  };
}
