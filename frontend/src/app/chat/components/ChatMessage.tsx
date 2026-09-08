"use client";

import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Pencil, Copy, Check, Bot } from "lucide-react";
import { toast } from "sonner";
import { FeedbackType, Message, TracerData } from "../types";
import { VoiceMessage } from "./VoiceMessage";
import ImageDisplay from "./ImageDisplay";
import VideoSegmentDisplay from "./VideoSegmentDisplay";
import Citations from "./Citations";
import FeedbackButtons from "./FeedbackButtons";
import ReadAloudButton from "./ReadAloudButton";

interface FeedbackState {
  liked: boolean | null;
  showFeedbackOptions: boolean;
  feedbackId: string | null;
  selectedFeedback: string[];
  likeDislikeButtonsRemoved?: boolean;
  categoricalOptionsRemoved?: boolean;
}

interface ChatMessageProps {
  message: Message;
  token: string;
  feedbackState?: FeedbackState;
  onLikeFeedback?: (messageId: number, requestId: number, isLike: boolean) => void;
  onCategoricalFeedback?: (messageId: number, feedbackType: FeedbackType) => void;
  onShowTrace?: (tracerJson: TracerData) => void;
  onDocumentDownload?: (documentId: number | string, fileName: string, pageNumber?: number) => void;
  onOpenSurvey?: () => void;
  onOpenDecisionSupport?: (message: Message) => void;
  onEditMessage?: (messageId: number, newText: string) => void;
  isEditing?: boolean;
  onStartEdit?: (messageId: number) => void;
  onCancelEdit?: () => void;
  isCallAgent?: boolean;
  disabled?: boolean;
  ttsEnabled?: boolean;
}

export default function ChatMessage({
  message,
  token,
  feedbackState,
  onLikeFeedback,
  onCategoricalFeedback,
  onShowTrace,
  onDocumentDownload,
  onOpenSurvey,
  onOpenDecisionSupport,
  onEditMessage,
  isEditing = false,
  onStartEdit,
  onCancelEdit,
  isCallAgent,
  disabled = false,
  ttsEnabled = true,
}: ChatMessageProps) {
  const [editText, setEditText] = useState(message.text);
  const [justCopied, setJustCopied] = useState(false);
  const editTextareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isEditing) {
      setEditText(message.text);
    }
  }, [isEditing, message.text]);

  useEffect(() => {
    if (!isEditing) return;
    const ta = editTextareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 240)}px`;
  }, [editText, isEditing]);

  useEffect(() => {
    if (isEditing) {
      editTextareaRef.current?.focus();
    }
  }, [isEditing]);

  const handleStartEdit = () => {
    onStartEdit?.(message.id);
  };

  const handleCancelEdit = () => {
    onCancelEdit?.();
  };

  const handleSaveEdit = () => {
    const trimmed = editText.trim();
    if (!trimmed || trimmed === message.text) {
      handleCancelEdit();
      return;
    }
    onEditMessage?.(message.id, trimmed);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSaveEdit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      handleCancelEdit();
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setJustCopied(true);
      setTimeout(() => setJustCopied(false), 1500);
    } catch {
      toast.error("Could not copy to clipboard.");
    }
  };

  const isUser = message.sender === "user";
  const canEdit = isUser && !!onEditMessage && !message.audioUrl;

  return (
    <div
      id={`message-${message.id}`}
      className={`group flex items-start gap-2 sm:gap-3 mb-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {!isUser && (
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-card border flex items-center justify-center flex-shrink-0 mt-1">
          <Bot className="w-4 h-4 text-muted-foreground" />
        </div>
      )}

      {/* Edit pencil for user messages — sits to the LEFT of the bubble, only on hover */}
      {isUser && canEdit && !isEditing && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={handleStartEdit}
          disabled={disabled}
          className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground mt-1 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 disabled:opacity-0 transition-opacity flex-shrink-0"
          aria-label="Edit message"
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      )}

      <div
        className={`${
          message.audioUrl
            ? "max-w-2xl"
            : `${isEditing ? "w-full max-w-2xl" : "p-3 rounded-lg max-w-2xl"} ${
                isUser && !isEditing ? "bg-primary text-primary-foreground" : "flex-1 min-w-0"
              }`
        } relative group`}
      >
        {isEditing && isUser ? (
          <div className="rounded-2xl bg-card border px-3 py-2 sm:px-4 sm:py-3">
            <Textarea
              ref={editTextareaRef}
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              onKeyDown={handleEditKeyDown}
              rows={1}
              aria-label="Edit message"
              className="min-h-[36px] max-h-[240px] resize-none border-0 bg-transparent shadow-none px-1 py-1 focus-visible:ring-0 focus-visible:ring-offset-0 text-sm"
            />
            <div className="flex items-center justify-end gap-2 mt-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleCancelEdit}
                className="h-8"
              >
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={handleSaveEdit}
                disabled={!editText.trim() || editText.trim() === message.text}
                className="h-8"
              >
                Send
              </Button>
            </div>
          </div>
        ) : message.audioUrl ? (
          <VoiceMessage audioUrl={message.audioUrl} isSender={isUser} />
        ) : (
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.text}
            </ReactMarkdown>
          </div>
        )}

        {/* Images */}
        {message.images && message.images.length > 0 && !isEditing && (
          <div className="mt-3 space-y-2">
            <span className="text-sm font-semibold text-foreground mb-2">
              {isUser ? "Your Images:" : "Supporting Images:"}
            </span>
            <div className="space-y-2">
              {message.images.map((image) => (
                <ImageDisplay
                  key={image.image_id}
                  image={image}
                  isUserImage={isUser}
                  onDocumentDownload={onDocumentDownload}
                />
              ))}
            </div>
          </div>
        )}

        {/* Video segments */}
        {message.video_segments && message.video_segments.length > 0 && (
          <div className="mt-3">
            <span className="text-sm font-semibold text-foreground mb-2 block">
              Related Videos:
            </span>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {message.video_segments.map((segment) => (
                <VideoSegmentDisplay
                  key={segment.segment_id}
                  segment={segment}
                />
              ))}
            </div>
          </div>
        )}

        {/* Citations for AI messages */}
        {!isUser && (
          <Citations message={message} onDocumentDownload={onDocumentDownload} />
        )}

        {/* Request ID for AI messages */}
        {!isUser && message.request_id > 0 && (
          <p className="mt-2 text-xs text-muted-foreground">
            Request ID: <code className="font-mono">{message.request_id}</code>
          </p>
        )}

        {/* Action row for AI messages */}
        {!isUser && feedbackState && onLikeFeedback && onCategoricalFeedback && (
          <div className="mt-4">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={handleCopy}
                className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground"
                aria-label={justCopied ? "Copied" : "Copy message"}
              >
                {justCopied ? (
                  <Check className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>

              <FeedbackButtons
                messageId={message.id}
                requestId={message.request_id}
                feedbackState={feedbackState}
                onLikeFeedback={onLikeFeedback}
                onCategoricalFeedback={onCategoricalFeedback}
              />

              {!isCallAgent && onOpenSurvey && message.request_id > 0 && (
                <Button size="sm" variant="outline" onClick={onOpenSurvey}>
                  End Chat Survey
                </Button>
              )}

              {isCallAgent && onOpenDecisionSupport && message.request_id > 0 && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onOpenDecisionSupport(message)}
                >
                  Decision Support
                </Button>
              )}
              {ttsEnabled && (
                <ReadAloudButton
                  responseId={message.id}
                  token={token}
                  language={message.original_language}
                />
              )}
              {onShowTrace && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onShowTrace(message.tracer_json)}
                >
                  Show Trace
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
