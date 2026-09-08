"use client";

import { useState, useEffect, useCallback } from "react";

interface Program { program_id: string; name: string; description?: string; }
interface Module { program_module_id: string; program_id: string; name: string; }
import { getPrograms, getProgramModules } from "../api";
import { toast } from "sonner";

export interface PDFPreviewState {
  isOpen: boolean;
  documentId: string | number | null;
  documentName: string;
  pageNumber: number;
}

interface UseSettingsProps {
  token: string | null;
}

export function useSettings({ token }: UseSettingsProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [useReference, setUseReference] = useState(true);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [documentModuleId, setDocumentModuleId] = useState("All modules");
  const [documentProgramId, setDocumentProgramId] = useState("All programs");
  const [pdfPreview, setPdfPreview] = useState<PDFPreviewState>({
    isOpen: false,
    documentId: null,
    documentName: "",
    pageNumber: 1,
  });

  const loadProgramsAndModules = useCallback(async () => {
    if (!token) return;

    try {
      const [programsResponse, modulesResponse] = await Promise.all([
        getPrograms(token),
        getProgramModules(token),
      ]);

      setPrograms(programsResponse.programs || []);
      setModules(modulesResponse.program_modules || []);
    } catch (error) {
      console.error("Failed to load programs and modules:", error);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      loadProgramsAndModules();
    }
  }, [token, loadProgramsAndModules]);

  const confirmSettings = (confirmed: {
    useReference: boolean;
    moduleId: string;
    programId: string;
  }) => {
    setUseReference(confirmed.useReference);
    setDocumentModuleId(confirmed.moduleId);
    setDocumentProgramId(confirmed.programId);

    const selectedModule = modules.find(
      (m) => String(m.program_module_id) === confirmed.moduleId
    );
    const selectedProgram = programs.find(
      (p) => String(p.program_id) === confirmed.programId
    );

    const activeDocuments = confirmed.useReference ? "Basic + Reference" : "Basic only";
    const moduleName = selectedModule?.name || "All modules";
    const programName = selectedProgram?.name || "All programs";

    toast.success(
      `Settings updated:\nDocuments: ${activeDocuments}\nModule: ${moduleName}\nProgram: ${programName}`
    );
  };

  // kept for backward compatibility with direct callers
  const handleSettingsUpdate = (overrides?: {
    useReference?: boolean;
    moduleId?: string;
    programId?: string;
  }) => {
    confirmSettings({
      useReference: overrides?.useReference ?? useReference,
      moduleId: overrides?.moduleId ?? documentModuleId,
      programId: overrides?.programId ?? documentProgramId,
    });
  };

  const handleDocumentDownload = (documentId: number | string, fileName: string, pageNumber?: number) => {
    const isValidId =
      typeof documentId === "number"
        || (typeof documentId === "string" && /^[a-zA-Z0-9_-]+$/.test(documentId));
    if (!isValidId) {
      toast.error("Invalid document ID.");
      return;
    }

    setPdfPreview({
      isOpen: true,
      documentId,
      documentName: fileName,
      pageNumber: pageNumber || 1,
    });
  };

  const closePdfPreview = () => {
    setPdfPreview({
      isOpen: false,
      documentId: null,
      documentName: "",
      pageNumber: 1,
    });
  };

  return {
    showSettings,
    setShowSettings,
    useReference,
    setUseReference,
    programs,
    modules,
    documentModuleId,
    setDocumentModuleId,
    documentProgramId,
    setDocumentProgramId,
    confirmSettings,
    handleSettingsUpdate,
    handleDocumentDownload,
    pdfPreview,
    closePdfPreview,
  };
}
