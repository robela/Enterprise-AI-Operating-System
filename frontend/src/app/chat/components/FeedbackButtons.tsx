"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { FeedbackType } from "../types";

// Feedback options with mutually exclusive groups (based on chainlit_app/app/feedback/followup.py)
const FEEDBACK_OPTIONS = [
  { value: "Too Short" as FeedbackType, label: "📏 Too Short", group: "length" },
  { value: "Too Long" as FeedbackType, label: "📏 Too Long", group: "length" },
  { value: "Fully Inaccurate" as FeedbackType, label: "❌ Fully Inaccurate", group: "accuracy" },
  { value: "Partially Inaccurate" as FeedbackType, label: "⚠️ Partially Inaccurate", group: "accuracy" },
  { value: "Not Clear" as FeedbackType, label: "🌐 Not Clear", group: "independent" },
  { value: "Not related to my work" as FeedbackType, label: "📝 Not related to my work", group: "independent" },
  { value: "Irrelevant" as FeedbackType, label: "🤔 Irrelevant", group: "independent" },
  { value: "Incorrect Program Documents Used" as FeedbackType, label: "📑 Incorrect Program Documents Used", group: "independent" },
  { value: "Bad Translation" as FeedbackType, label: "🗣️ Bad Translation", group: "independent" },
];

interface FeedbackState {
  liked: boolean | null;
  showFeedbackOptions: boolean;
  feedbackId: string | null;
  selectedFeedback: string[];
  likeDislikeButtonsRemoved?: boolean;
  categoricalOptionsRemoved?: boolean;
}

interface FeedbackButtonsProps {
  messageId: number;
  requestId: number;
  feedbackState: FeedbackState;
  onLikeFeedback: (messageId: number, requestId: number, isLike: boolean) => void;
  onCategoricalFeedback: (messageId: number, feedbackType: FeedbackType) => void;
}

export default function FeedbackButtons({
  messageId,
  requestId,
  feedbackState,
  onLikeFeedback,
  onCategoricalFeedback
}: FeedbackButtonsProps) {
  // Show nothing if initial state isn't set up
  if (!feedbackState) return null;

  return (
    <div className="space-y-2">
      {/* Like/Dislike Buttons - shown until any feedback is given */}
      {!feedbackState.likeDislikeButtonsRemoved && (
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant={feedbackState.liked === true ? "default" : "outline"}
            onClick={() => onLikeFeedback(messageId, requestId, true)}
            disabled={feedbackState.liked !== null}
            className="h-8 px-3"
          >
            <ThumbsUp className="mr-1 h-3.5 w-3.5" />
            Like
          </Button>
          <Button
            size="sm"
            variant={feedbackState.liked === false ? "default" : "outline"}
            onClick={() => onLikeFeedback(messageId, requestId, false)}
            disabled={feedbackState.liked !== null}
            className="h-8 px-3"
          >
            <ThumbsDown className="mr-1 h-3.5 w-3.5" />
            Dislike
          </Button>
        </div>
      )}

      {/* Thank you message for likes */}
      {feedbackState.liked === true && feedbackState.likeDislikeButtonsRemoved && (
        <div className="text-gray-600 text-sm font-medium">
          Thank you for your feedback!
        </div>
      )}

      {/* Categorical feedback options - shown after dislike */}
      {feedbackState.showFeedbackOptions && !feedbackState.categoricalOptionsRemoved && (
        <div className="space-y-2">
          <p className="text-sm text-gray-600">
            We&apos;re sorry the response wasn&apos;t helpful. Could you tell us more? (Multiple selections allowed)
          </p>
          <div className="flex flex-wrap gap-1">
            {FEEDBACK_OPTIONS.map((option) => {
              const isSelected = feedbackState.selectedFeedback.includes(option.value);

              // Check if this option should be hidden due to mutual exclusion
              const shouldHide = option.group !== "independent" && feedbackState.selectedFeedback.some(feedback => {
                const selectedOption = FEEDBACK_OPTIONS.find(opt => opt.value === feedback);
                return selectedOption?.group === option.group && selectedOption?.value !== option.value;
              });

              if (shouldHide) return null;

              return (
                <Button
                  key={option.value}
                  size="sm"
                  variant={isSelected ? "default" : "outline"}
                  className="h-8 px-2.5 text-xs"
                  onClick={() => onCategoricalFeedback(messageId, option.value)}
                  disabled={isSelected}
                >
                  {option.label}
                </Button>
              );
            })}
          </div>
        </div>
      )}

      {/* Thank you message for completed categorical feedback */}
      {feedbackState.categoricalOptionsRemoved && feedbackState.selectedFeedback.length > 0 && (
        <div className="text-green-600 text-sm font-medium">
          Thank you for your detailed feedback!
        </div>
      )}
    </div>
  );
}
