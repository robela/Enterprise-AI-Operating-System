"use client";

import { useState, useCallback } from "react";
import { FeedbackType } from "../types";
import { submitLikeFeedback, submitCategoricalFeedback } from "../api";
import { toast } from "sonner";

interface FeedbackState {
  liked: boolean | null;
  showFeedbackOptions: boolean;
  feedbackId: string | null;
  selectedFeedback: string[];
  likeDislikeButtonsRemoved?: boolean;
  categoricalOptionsRemoved?: boolean;
}

// Feedback options with mutual exclusion groups - mirrors  chainlit_app/app/feedback/followup.py
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

interface UseFeedbackProps {
  token: string | null;
}

const createDefaultFeedbackState = (): FeedbackState => ({
  liked: null,
  showFeedbackOptions: false,
  feedbackId: null,
  selectedFeedback: [],
  likeDislikeButtonsRemoved: false,
  categoricalOptionsRemoved: false,
});

export function useFeedback({ token }: UseFeedbackProps) {
  const [feedbackStates, setFeedbackStates] = useState<Record<number, FeedbackState>>({});

  const handleLikeFeedback = async (messageId: number, requestId: number, isLike: boolean) => {
    if (!token) return;

    try {
      const response = await submitLikeFeedback({
        request_id: requestId,
        is_like: isLike,
      }, token);

      if (isLike) {
        // Like: Remove all buttons and show confirmation
        setFeedbackStates((prev) => {
          const current = prev[messageId] ?? createDefaultFeedbackState();
          return {
            ...prev,
            [messageId]: {
              ...current,
              liked: true,
              likeDislikeButtonsRemoved: true,
              showFeedbackOptions: false,
              feedbackId: response.saved_feedback_id,
            },
          };
        });
      } else {
        // Dislike: Remove like/dislike buttons, show categorical options (
        setFeedbackStates((prev) => {
          const current = prev[messageId] ?? createDefaultFeedbackState();
          return {
            ...prev,
            [messageId]: {
              ...current,
              liked: false,
              likeDislikeButtonsRemoved: true,
              showFeedbackOptions: true,
              feedbackId: response.saved_feedback_id,
            },
          };
        });
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
      toast.error("Failed to submit feedback.");
    }
  };

  const handleCategoricalFeedback = async (messageId: number, feedbackType: FeedbackType) => {
    const feedbackState = feedbackStates[messageId];
    if (!feedbackState?.feedbackId || !token) return;

    try {
      await submitCategoricalFeedback({
        feedback_id: feedbackState.feedbackId,
        feedback_type_name: feedbackType,
      }, token);

      // Find the selected option to determine its group
      const selectedOption = FEEDBACK_OPTIONS.find(opt => opt.value === feedbackType);
      const selectedGroup = selectedOption?.group;

      setFeedbackStates((prev) => {
        const current = prev[messageId] ?? createDefaultFeedbackState();
        const currentFeedback = prev[messageId]?.selectedFeedback || [];
        let updatedFeedback = [...currentFeedback];

        // Only apply mutual exclusion for non-independent groups
        if (selectedGroup && selectedGroup !== "independent") {
          // Remove other selections from the same group
          updatedFeedback = updatedFeedback.filter(feedback => {
            const existingOption = FEEDBACK_OPTIONS.find(opt => opt.value === feedback);
            return existingOption?.group !== selectedGroup;
          });
        }

        // Add the new selection
        updatedFeedback.push(feedbackType);

        return {
          ...prev,
          [messageId]: {
            ...current,
            selectedFeedback: updatedFeedback,
          },
        };
      });

      toast.success(`Feedback received: ${feedbackType}`);
    } catch (error) {
      console.error("Error submitting categorical feedback:", error);
      toast.error("Failed to submit feedback.");
    }
  };

  // Initialize feedback state for a new message
  const initializeFeedbackState = useCallback((messageId: number) => {
    setFeedbackStates((prev) => ({
      ...prev,
      [messageId]: createDefaultFeedbackState(),
    }));
  }, []);

  const resetFeedbackStates = () => {
    setFeedbackStates({});
  };

  return {
    feedbackStates,
    handleLikeFeedback,
    handleCategoricalFeedback,
    initializeFeedbackState,
    resetFeedbackStates,
  };
}
