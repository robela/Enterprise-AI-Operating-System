interface ChatImage {
  image_id: number;
  image_data: string;
  caption: string;
  document_name: string;
  page_number: number;
  document_id: number;
}

interface ChatVideoSegment {
  segment_id: number;
  source_url: string;
  title: string;
  topic: string;
  start_sec: number;
  end_sec: number;
}

interface Message {
  id: number;
  text: string;
  chat_id: string | null;
  sender: "user" | "ai";
  tracer_json: TracerData;
  request_id: number;
  response_metadata?: {
    chunks: Record<string, {
      document_id: string;
      file_name: string;
      page_num_within_doc: number;
    }>;
  };
  images?: ChatImage[];
  video_segments?: ChatVideoSegment[];
  original_language?: string;
  timestamp: Date;
  audioUrl?: string;
}

interface TracerStep {
  timestamp: string;
  name: string;
  [key: string]: unknown;
}

interface TracerData {
  [stepKey: string]: TracerStep;
}

export type FeedbackType =
  | "Too Short"
  | "Too Long"
  | "Fully Inaccurate"
  | "Partially Inaccurate"
  | "Not Clear"
  | "Not related to my work"
  | "Irrelevant"
  | "Incorrect Program Documents Used"
  | "Bad Translation";

interface ConversationSummary {
  chat_id: string;
  title: string;
  sector?: string;
  last_updated: string;
  message_count: number;
}

interface ConversationListResponse {
  conversations: ConversationSummary[];
  total_count: number;
}

export type { Message, TracerData, ChatImage, ChatVideoSegment, ConversationSummary, ConversationListResponse };
