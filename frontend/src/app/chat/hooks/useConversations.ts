"use client";

import { useEffect, useState, useCallback } from "react";
import { getConversations, deleteConversation as deleteConversationApi } from "../api";
import { ConversationSummary } from "../types";
import { toast } from "sonner";

export function useConversations(token: string | null, sector: string | null) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const fetch = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const convs = await getConversations(token, sector);
      setConversations(convs);
    } catch {
      // silently fail — sidebar is non-critical
    } finally {
      setLoading(false);
    }
  }, [token, sector]);

  useEffect(() => { fetch(); }, [fetch]);

  const deleteConversation = async (id: string) => {
    try {
      if (!token) return;
      await deleteConversationApi(id, token);
      setConversations((prev) => prev.filter((c) => c.chat_id !== id));
      toast.success("Conversation deleted");
    } catch {
      toast.error("Failed to delete conversation");
    }
  };

  return { conversations, loading, fetch, deleteConversation };
}
