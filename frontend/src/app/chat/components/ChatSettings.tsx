"use client";

import React, { useState, useEffect } from "react";
import { Info } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Program {
  program_id: string | number;
  name: string;
  description?: string;
  program_module_id?: string | number;
}

interface Module {
  program_module_id: string | number;
  program_id: string | number;
  name: string;
}

interface ChatSettingsProps {
  open: boolean;
  onClose: () => void;
  useReference: boolean;
  documentModuleId: string;
  documentProgramId: string;
  programs: Program[];
  modules: Module[];
  onConfirm: (settings: {
    useReference: boolean;
    moduleId: string;
    programId: string;
  }) => void;
}

function LabelWithTooltip({
  children,
  tooltip,
}: {
  children: React.ReactNode;
  tooltip: string;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <Label className="text-sm font-medium">{children}</Label>
      <Tooltip>
        <TooltipTrigger asChild>
          <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help shrink-0" />
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[220px] text-center">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </div>
  );
}

export default function ChatSettings({
  open,
  onClose,
  useReference,
  documentModuleId,
  documentProgramId,
  programs,
  modules,
  onConfirm,
}: ChatSettingsProps) {
  const [pendingUseReference, setPendingUseReference] = useState(useReference);
  const [pendingModuleId, setPendingModuleId] = useState(documentModuleId);
  const [pendingProgramId, setPendingProgramId] = useState(documentProgramId);

  // Sync pending state from committed values each time the dialog opens
  useEffect(() => {
    if (open) {
      setPendingUseReference(useReference);
      setPendingModuleId(documentModuleId);
      setPendingProgramId(documentProgramId);
    }
  }, [open, useReference, documentModuleId, documentProgramId]);

  const programGroups =
    pendingModuleId === "All modules"
      ? modules
      : modules.filter(
          (m) => String(m.program_module_id) === pendingModuleId
        );

  const handleModuleChange = (value: string) => {
    setPendingModuleId(value);
    if (value !== "All modules") {
      const stillValid = programs.find(
        (p) =>
          String(p.program_id) === pendingProgramId &&
          String(p.program_module_id) === value
      );
      if (!stillValid) setPendingProgramId("All programs");
    }
  };

  const handleProgramChange = (value: string) => {
    setPendingProgramId(value);
    const match = programs.find((p) => String(p.program_id) === value);
    if (match) {
      const moduleId = String(match.program_module_id);
      if (moduleId !== pendingModuleId) setPendingModuleId(moduleId);
    }
  };

  const handleReset = () => {
    setPendingUseReference(true);
    setPendingModuleId("All modules");
    setPendingProgramId("All programs");
  };

  const handleConfirm = () => {
    onConfirm({
      useReference: pendingUseReference,
      moduleId: pendingModuleId,
      programId: pendingProgramId,
    });
    onClose();
  };

  return (
    <TooltipProvider delayDuration={200}>
      <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
        <DialogContent className="
          flex flex-col gap-0
          w-[calc(100%-2rem)] sm:w-full sm:max-w-md
          max-h-[90dvh]
          p-4 sm:p-6
          overflow-hidden
          rounded-lg
        ">
          {/* Header — always visible */}
          <DialogHeader className="shrink-0 pb-3 sm:pb-4">
            <DialogTitle>Settings panel</DialogTitle>
          </DialogHeader>

          {/* Scrollable body */}
          <div className="flex-1 min-h-0 overflow-y-auto space-y-4 sm:space-y-5 pr-1 pb-6">
            {/* Reference Documents Toggle */}
            <div className="flex items-center justify-between gap-4">
              <Label
                htmlFor="reference-toggle"
                className="text-sm font-medium cursor-pointer leading-snug"
              >
                Also use reference documents
              </Label>
              <Switch
                id="reference-toggle"
                checked={pendingUseReference}
                onCheckedChange={setPendingUseReference}
              />
            </div>

            {/* Module Filter */}
            <div className="space-y-1.5">
              <LabelWithTooltip tooltip="Only documents belonging to the selected module will be searched">
                Module filter
              </LabelWithTooltip>
              <Select value={pendingModuleId} onValueChange={handleModuleChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All modules" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All modules">All modules</SelectItem>
                  {modules.map((module) => (
                    <SelectItem
                      key={module.program_module_id}
                      value={String(module.program_module_id)}
                    >
                      <span className="break-words whitespace-normal max-w-[260px] sm:max-w-[300px] block">
                        {module.name}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Note: If you select a program below, the module filter will be ignored.
              </p>
            </div>

            {/* Program Filter */}
            <div className="space-y-1.5">
              <LabelWithTooltip tooltip="Only documents belonging to the selected program will be searched">
                Program filter
              </LabelWithTooltip>
              <Select value={pendingProgramId} onValueChange={handleProgramChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="All programs" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="All programs">All programs</SelectItem>
                  {programGroups
                    .filter((module) =>
                      programs.some(
                        (p) => p.program_module_id === module.program_module_id
                      )
                    )
                    .map((module, index) => {
                      const groupedPrograms = programs.filter(
                        (p) => p.program_module_id === module.program_module_id
                      );
                      return (
                        <React.Fragment key={module.program_module_id}>
                          {index > 0 && <SelectSeparator />}
                          <SelectGroup>
                            <SelectLabel className="font-semibold break-words whitespace-normal max-w-[260px] sm:max-w-[300px] block">
                              {module.name}
                            </SelectLabel>
                            {groupedPrograms.map((program) => (
                              <SelectItem
                                key={program.program_id}
                                value={String(program.program_id)}
                              >
                                <span className="break-words whitespace-normal max-w-[260px] sm:max-w-[300px] block">
                                  {program.name}
                                </span>
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </React.Fragment>
                      );
                    })}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Footer — always visible, pinned at bottom */}
          <DialogFooter className="shrink-0 flex-row items-center justify-between gap-2 sm:justify-between pt-3 sm:pt-4 mt-1 border-t">
            <Button variant="outline" size="sm" onClick={handleReset}>
              Reset
            </Button>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleConfirm}>Confirm</Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}
