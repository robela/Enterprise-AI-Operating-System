"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/services/api/client";

interface GlobalSettings {
  sttEnabled: boolean;
  ttsEnabled: boolean;
}

const DEFAULTS: GlobalSettings = { sttEnabled: true, ttsEnabled: true };

export function useGlobalSettings(token: string | null): GlobalSettings {
  const [settings, setSettings] = useState<GlobalSettings>(DEFAULTS);

  useEffect(() => {
    if (!token) return;
    apiClient
      .get("/api/v1/settings/global")
      .then((res) => {
        setSettings({
          sttEnabled: res.data.stt_enabled ?? true,
          ttsEnabled: res.data.tts_enabled ?? true,
        });
      })
      .catch(() => {
        // Fail open — if settings can't be fetched, show both features
      });
  }, [token]);

  return settings;
}
