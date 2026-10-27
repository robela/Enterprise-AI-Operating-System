"use client";

import React, { Suspense, useState, useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/utils/auth";
import { Plus } from "lucide-react";

import ChatSettings from "./components/ChatSettings";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import PopUpModal from "./components/PopUpModal";
import TracerModal from "./components/Tracer";
import TypingAnimation from "./components/TypingAnimation";
import SurveyDialog from "./components/SurveyDialog";
import DecisionSupportSheet from "./components/DecisionSupportSheet";

import { useChat } from "./hooks/useChat";
import { useFeedback } from "./hooks/useFeedback";
import { useSettings } from "./hooks/useSettings";
import { useSurvey } from "./hooks/useSurvey";
import { useDecisionSupport } from "./hooks/useDecisionSupport";
import { Message } from "./types";

function ChatInterface() {
  const [isClient, setIsClient] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { token, user_id, role, username } = useAuth();
  const isCallAgent = role === "callAgent";
  const isAdmin = role === "admin";
  const requestedChatId = searchParams.get("chat_id");
  const activeSector = (searchParams.get("sector") || "general").trim().toLowerCase();
  const startNewConversation = searchParams.get("new") === "1";

  const chat = useChat({ token, userId: user_id, isAdmin: isAdmin ?? false });
  const {
    feedbackStates,
    handleLikeFeedback,
    handleCategoricalFeedback,
    initializeFeedbackState,
    resetFeedbackStates,
  } = useFeedback({ token });
  const settings = useSettings({ token });
  const survey = useSurvey({ token });
  const decisionSupport = useDecisionSupport({ token });

  useEffect(() => { setIsClient(true); }, []);

  useEffect(() => {
    if (!isClient) return;
    if (startNewConversation) {
      chat.clearChat();
      resetFeedbackStates();
      router.replace(`${pathname}?sector=${encodeURIComponent(activeSector)}`);
      return;
    }
    if (!requestedChatId) return;
    if (requestedChatId !== chat.chatId) {
      void (async () => {
        await chat.loadChatHistory(requestedChatId);
        resetFeedbackStates();
      })();
    }
  }, [isClient, startNewConversation, requestedChatId, chat.chatId, router, pathname, activeSector]);

  useEffect(() => {
    if (!isClient || !chat.chatId || startNewConversation || requestedChatId) return;
    router.replace(`/chat?chat_id=${chat.chatId}&sector=${encodeURIComponent(activeSector)}`);
  }, [isClient, chat.chatId, requestedChatId, startNewConversation, router, pathname, activeSector]);

  useEffect(() => {
    const lastMessage = chat.messages[chat.messages.length - 1];
    if (lastMessage && lastMessage.sender === "ai" && lastMessage.request_id) {
      initializeFeedbackState(lastMessage.id);
    }
  }, [chat.messages, initializeFeedbackState]);

  const handleClearChat = () => {
    router.replace(`${pathname}?sector=${encodeURIComponent(activeSector)}`);
    chat.clearChat();
    resetFeedbackStates();
  };

  const handleSurveyComplete = () => {
    router.replace(`${pathname}?sector=${encodeURIComponent(activeSector)}`);
    chat.clearChat();
    resetFeedbackStates();
  };

  const handleOpenDecisionSupport = (message: Message) => {
    if (!chat.chatId) return;
    const msgIndex = chat.messages.findIndex((m) => m.id === message.id);
    const prevMessage = msgIndex > 0 ? chat.messages[msgIndex - 1] : null;
    const question = prevMessage?.sender === "user" ? prevMessage.text : "";
    decisionSupport.openSheet(chat.chatId, message.request_id, question, message.text);
  };

  const handleDecisionSupportComplete = () => {
    router.replace(`${pathname}?sector=${encodeURIComponent(activeSector)}`);
    chat.clearChat();
    resetFeedbackStates();
  };

  const handleSendMessage = async () => {
    await chat.handleSendMessage(
      settings.useReference,
      settings.documentModuleId,
      settings.documentProgramId,
      activeSector
    );
  };

  const handleClinicalFollowUp = (text: string) => {
    void chat.sendClinicalFollowUp(
      text,
      settings.useReference,
      settings.documentModuleId,
      settings.documentProgramId,
      activeSector,
    );
  };

  const handleEditMessage = (messageId: number, newText: string) => {
    setEditingMessageId(null);
    chat.editAndResend(messageId, newText, settings.useReference, settings.documentModuleId, settings.documentProgramId, activeSector);
  };

  const handleRecordingComplete = async (blob: Blob, contentType: string, language: "am" | "om") => {
    const transcript = await chat.handleTranscribeAudio(blob, contentType, language);
    if (transcript) chat.setNewMessage(transcript);
  };

  const handleStartNewConversation = () => {
    setEditingMessageId(null);
    router.replace(`${pathname}?new=1&sector=${encodeURIComponent(activeSector)}`);
  };

  if (!isClient) {
    return <div className="p-6 text-sm text-muted-foreground">Loading chat...</div>;
  }

  return (
    <div className="flex h-full w-full bg-background overflow-hidden">
      <div className="flex flex-col min-w-[320px] flex-1 transition-all duration-300 h-full overflow-hidden">
        <div className="px-6 pt-5 pb-4 shrink-0 flex items-center justify-between gap-3">
          <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
          <Button type="button" size="sm" onClick={handleStartNewConversation} className="gap-2">
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        <div className="flex flex-1 min-h-0 px-4 pb-4">
          <div className="flex flex-col flex-1 mx-auto w-full max-w-3xl min-h-0">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {chat.messages.length === 0 && !chat.loading && (
                <div className="flex flex-col items-center justify-center text-center px-4 py-8 sm:py-12 md:py-16">
                  <div className="w-14 h-14 rounded-full bg-card border flex items-center justify-center mb-4 text-2xl">
                    AI
                  </div>
                  <p className="mt-2 text-sm sm:text-base text-muted-foreground max-w-md">
                    Hello{username ? `, ${username}` : ""}! I am your Enterprise AI assistant. How may I assist you today?
                  </p>
                </div>
              )}

              {chat.messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  token={token!}
                  feedbackState={feedbackStates[message.id]}
                  onLikeFeedback={handleLikeFeedback}
                  onCategoricalFeedback={handleCategoricalFeedback}
                  onShowTrace={isAdmin ? chat.handleShowTrace : undefined}
                  onDocumentDownload={settings.handleDocumentDownload}
                  onOpenSurvey={survey.openSurvey}
                  onOpenDecisionSupport={handleOpenDecisionSupport}
                  onEditMessage={handleEditMessage}
                  onSubmitClinicalFollowUp={handleClinicalFollowUp}
                  isEditing={editingMessageId === message.id}
                  onStartEdit={setEditingMessageId}
                  onCancelEdit={() => setEditingMessageId(null)}
                  isCallAgent={isCallAgent}
                  disabled={chat.loading}
                  ttsEnabled={false}
                />
              ))}

              {chat.loading && (
                <div className="flex items-center gap-2 sm:gap-3 mb-4">
                  <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 text-xs font-semibold">
                    AI
                  </div>
                  <TypingAnimation />
                </div>
              )}

              <div ref={chat.messagesEndRef} />
            </div>
          </ScrollArea>

          <ChatSettings
            open={settings.showSettings}
            onClose={() => settings.setShowSettings(false)}
            useReference={settings.useReference}
            documentModuleId={settings.documentModuleId}
            documentProgramId={settings.documentProgramId}
            programs={settings.programs}
            modules={settings.modules}
            onConfirm={settings.confirmSettings}
          />

          <div className="shrink-0 w-full flex flex-col pb-4 px-4">
            <ChatInput
              value={chat.newMessage}
              onChange={chat.setNewMessage}
              onSubmit={handleSendMessage}
              onCancelGeneration={chat.cancelGeneration}
              onToggleSettings={() => settings.setShowSettings(!settings.showSettings)}
              onClearChat={handleClearChat}
              onRecordingComplete={handleRecordingComplete}
              disabled={!token || !user_id}
              loading={chat.loading}
              sttEnabled={true}
            />
          </div>

          {chat.showTraceModal && (
            <PopUpModal onClose={() => chat.setShowTraceModal(false)}>
              <TracerModal tracerData={chat.selectedTraceData} />
            </PopUpModal>
          )}

          {decisionSupport.isOpen && (
            <PopUpModal onClose={decisionSupport.closeSheet} maxWidthClass="max-w-xl">
              <DecisionSupportSheet hook={decisionSupport} onComplete={handleDecisionSupportComplete} />
            </PopUpModal>
          )}

          <SurveyDialog
            isOpen={survey.isOpen}
            step={survey.step}
            actionTaken={survey.actionTaken}
            intentChanged={survey.intentChanged}
            isSaving={survey.isSaving}
            onActionTaken={survey.handleActionTaken}
            onIntentChanged={(value) => survey.handleIntentChanged(value, chat.chatId, handleSurveyComplete)}
            onClose={survey.closeSurvey}
          />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading chat...</div>}>
      <ChatInterface />
    </Suspense>
  );
}
