import axios from "axios";
import { Message, ConversationSummary } from "./types";

const BASE =
  typeof window === "undefined" ? process.env.NEXT_PUBLIC_BACKEND_URL?.trim() || "http://localhost:8060" : "";
const client = axios.create({ baseURL: BASE, timeout: 30000 });
client.interceptors.request.use((cfg) => {
  if (typeof window !== "undefined") {
    const t = localStorage.getItem("token");
    if (t) cfg.headers.Authorization = `Bearer ${t}`;
  }
  return cfg;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("tenant_id");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// ─── Chat ────────────────────────────────────────────────────────────────────

interface GetChatResponseParams {
  token: string;
  chat_id: string | null;
  user_id: string | number | null;
  message: string;
  sector?: string | null;
  document_modules?: number[] | null;
  document_programs?: number[] | null;
  signal?: AbortSignal;
  trace?: boolean;
}

export interface DecisionSupportPayload {
  chat_id: string;
  request_id: number;
  question_prompt: string;
  ai_answer: string;
  action_taken: "managed" | "referred";
  intent_changed: boolean;
  hew?: string | null;
  language_preference?: string | null;
  program?: string | null;
  tag?: string | null;
}

export interface TagOut {
  tag_id: number;
  name: string;
  description?: string | null;
}

export interface TagCategoryOut {
  category: {
    category_id: number;
    name: string;
  };
  children: TagOut[];
}

export interface GroupedTagsOut {
  categories: TagCategoryOut[];
}

export const getChatResponse = async (params: GetChatResponseParams): Promise<Message> => {
  const { data } = await client.post(
    "/api/v1/ai/chat",
    {
      message: params.message,
      conversation_id: params.chat_id,
      sector: params.sector ?? null,
      provider: "mock",
      stream: false,
    },
    { signal: params.signal }
  );

  return {
    id: Date.now(),
    text: data.answer || "",
    chat_id: data.conversation_id || params.chat_id,
    sender: "ai",
    request_id: 0,
    tracer_json: data.trace || {},
    response_metadata: { chunks: {} },
    completeness: data.completeness,
    images: [],
    video_segments: [],
    timestamp: new Date(),
  };
};

export const transcribeAudio = async (params: {
  file: Blob;
  contentType: string;
  languageCode: "am" | "om";
  token: string;
}): Promise<{ transcript: string }> => {
  const formData = new FormData();
  formData.append("file", params.file, "audio.webm");
  formData.append("language", params.languageCode);
  const { data } = await client.post("/api/v1/ai/chat/transcribe", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return { transcript: data.text || "" };
};

export const synthesizeSpeech = async (
  responseId: number,
  token: string,
  language: string = "en"
): Promise<Blob> => {
  const { data } = await client.post(
    "/api/v1/ai/chat/text-to-speech",
    {
      // Backend currently exposes text-based TTS; keep signature compatible with callers.
      text: `Response ${responseId}`,
      language,
    },
    { responseType: "blob" }
  );
  return data as Blob;
};

export const getChatHistory = async (
  chatId: string,
  token: string,
  signal?: AbortSignal
): Promise<Message[]> => {
  try {
    const { data } = await client.get(`/api/v1/ai/chat/conversations/${chatId}`, { signal });
    const messages: Message[] = (data.messages || []).map((msg: { id: string; role: string; content: string; created_at?: string }, idx: number) => ({
      id: idx + 1,
      text: msg.content,
      chat_id: chatId,
      sender: msg.role === "user" ? "user" : "ai",
      request_id: idx,
      tracer_json: {},
      response_metadata: { chunks: {} },
      images: [],
      timestamp: new Date(msg.created_at || Date.now()),
    }));
    return messages;
  } catch {
    return [];
  }
};

export const getConversations = async (
  token: string,
  sector?: string | null
): Promise<ConversationSummary[]> => {
  const { data } = await client.get("/api/v1/ai/chat/conversations/list", {
    params: sector ? { sector } : undefined,
  });
  return (data || []).map((conv: {
    id: string;
    title?: string;
    sector?: string;
    updated_at?: string;
    last_updated?: string;
    message_count?: number;
  }) => ({
    chat_id: conv.id,
    title: conv.title || "Untitled",
    sector: conv.sector,
    last_updated: conv.last_updated || conv.updated_at || new Date().toISOString(),
    message_count: conv.message_count ?? 0,
  }));
};

export const deleteConversation = async (
  chatId: string,
  token: string
): Promise<void> => {
  await client.delete(`/api/v1/ai/chat/conversations/${chatId}`);
};

export const getGroupedTags = async (token: string): Promise<GroupedTagsOut> => {
  try {
    const { data } = await client.get("/api/v1/feedback/dislike-options");
    const options = Array.isArray(data) ? data : [];

    const grouped = new Map<string, TagOut[]>();
    options.forEach((item: {
      id?: string | number;
      name?: string;
      category?: string;
      description?: string | null;
    }, index: number) => {
      const category = (item.category || "General").trim() || "General";
      const tagList = grouped.get(category) || [];
      const numericId =
        typeof item.id === "number"
          ? item.id
          : Number.parseInt(String(item.id ?? index + 1), 10);

      tagList.push({
        tag_id: Number.isNaN(numericId) ? index + 1 : numericId,
        name: item.name || "Unnamed",
        description: item.description ?? null,
      });
      grouped.set(category, tagList);
    });

    const categories: TagCategoryOut[] = Array.from(grouped.entries()).map(
      ([categoryName, tags], index) => ({
        category: {
          category_id: index + 1,
          name: categoryName,
        },
        children: tags,
      })
    );

    return { categories };
  } catch {
    return { categories: [] };
  }
};

export const submitDecisionSupport = async (
  payload: DecisionSupportPayload,
  token: string
): Promise<{ status: "ok" }> => {
  await client.post("/api/v1/feedback/survey", {
    conversation_id: payload.chat_id,
    action_taken: [payload.action_taken],
    intent_changed: payload.intent_changed,
    additional_feedback: JSON.stringify({
      request_id: payload.request_id,
      question_prompt: payload.question_prompt,
      ai_answer: payload.ai_answer,
      hew: payload.hew ?? null,
      language_preference: payload.language_preference ?? null,
      program: payload.program ?? null,
      tag: payload.tag ?? null,
    }),
  });
  return { status: "ok" };
};

export const submitDecisionSurvey = async (
  payload: { chat_id: string; action_taken: "managed" | "referred"; intent_changed: boolean },
  token: string
): Promise<{ status: "ok" }> => {
  await client.post("/api/v1/feedback/survey", {
    conversation_id: payload.chat_id,
    action_taken: [payload.action_taken],
    intent_changed: payload.intent_changed,
  });
  return { status: "ok" };
};

export const getPDFFile = async (params: {
  token: string;
  document_id: number;
}): Promise<Blob> => {
  const { data } = await client.get(`/api/v1/documents/${params.document_id}/download`, {
    responseType: "blob",
  });
  return data as Blob;
};

// ─── Feedback ────────────────────────────────────────────────────────────────

export const submitLikeFeedback = async (
  feedbackData: { request_id: number; is_like: boolean },
  token: string
): Promise<{ saved_feedback_id: string }> => {
  try {
    const { data } = await client.post("/api/v1/feedback/like", {
      message_id: String(feedbackData.request_id),
      liked: feedbackData.is_like,
    });
    return { saved_feedback_id: data.feedback_id || `fb-${Date.now()}` };
  } catch {
    return { saved_feedback_id: `fb-${Date.now()}` };
  }
};

export const submitCategoricalFeedback = async (
  feedbackData: { feedback_id: string; feedback_type_name: string },
  token: string
): Promise<{ categorical_feedback_type_name: string }> => {
  try {
    await client.post("/api/v1/feedback/categorical", {
      feedback_id: feedbackData.feedback_id,
      feedback_tags: [feedbackData.feedback_type_name],
    });
    return { categorical_feedback_type_name: feedbackData.feedback_type_name };
  } catch {
    return { categorical_feedback_type_name: feedbackData.feedback_type_name };
  }
};

// ─── Programs & Modules ──────────────────────────────────────────────────────

export const getPrograms = async (token: string): Promise<{ programs: { program_id: string; name: string; description?: string }[] }> => {
  try {
    const { data } = await client.get("/api/v1/ai/programs");
    return { programs: (data || []).map((p: { id: string; name: string; description?: string }) => ({ program_id: p.id, name: p.name, description: p.description })) };
  } catch {
    return { programs: [] };
  }
};

export const getProgramModules = async (token: string): Promise<{ program_modules: { program_module_id: string; program_id: string; name: string }[] }> => {
  try {
    const { data } = await client.get("/api/v1/ai/program-modules");
    return { program_modules: (data || []).map((m: { id: string; program_id: string; name: string }) => ({ program_module_id: m.id, program_id: m.program_id, name: m.name })) };
  } catch {
    return { program_modules: [] };
  }
};

export { getChatResponse as default };
