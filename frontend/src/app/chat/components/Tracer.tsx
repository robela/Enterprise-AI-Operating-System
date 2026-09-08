"use client";

import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { TracerData } from "../types";

function computeTimeTaken(prevTimestamp: string | undefined, currentTimestamp: string | undefined) {
  if (!prevTimestamp || !currentTimestamp) return "N/A";
  try {
    const t1 = new Date(prevTimestamp).getTime();
    const t2 = new Date(currentTimestamp).getTime();
    const diffSec = (t2 - t1) / 1000;
    return diffSec.toFixed(2) + "s";
  } catch {
    return "N/A";
  }
}

interface TracerModalProps {
  tracerData: TracerData | null;
}

export default function TracerModal({ tracerData }: TracerModalProps) {
  const [expandedSteps, setExpandedSteps] = useState<string[]>([]);

  const toggleStep = (stepKey: string) => {
    setExpandedSteps((prev) =>
      prev.includes(stepKey) ? prev.filter((k) => k !== stepKey) : [...prev, stepKey],
    );
  };

  // Sort step keys (e.g., "Step0", "Step1", etc.) by numeric value
  const sortedSteps = tracerData
    ? Object.keys(tracerData).sort((a, b) => {
        const numA = parseInt(a.replace(/\D+/g, ""), 10);
        const numB = parseInt(b.replace(/\D+/g, ""), 10);
        return numA - numB;
      })
    : [];

  let prevTimestamp: string | undefined;

  return (
    <div className="flex flex-col h-full w-full">
      <ScrollArea className="flex-grow p-4 w-full">
        {tracerData && sortedSteps.length > 0 ? (
          sortedSteps.map((stepKey) => {
            const stepValue = { ...tracerData[stepKey] };
            const { name, ...stepValueWithoutName } = stepValue;

            const currentTimestamp = stepValue?.timestamp;
            const timeTaken = computeTimeTaken(prevTimestamp, currentTimestamp);
            prevTimestamp = currentTimestamp;

            const isExpanded = expandedSteps.includes(stepKey);
            const stepNumber = stepKey.replace(/\D+/g, "");

            return (
              <div
                key={stepKey}
                className="mb-4 flex flex-col items-start border rounded-lg"
              >
                <div
                  className="bg-secondary text-secondary-foreground w-full flex items-center justify-between p-3 rounded-t-lg cursor-pointer"
                  onClick={() => toggleStep(stepKey)}
                >
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">
                      {stepNumber}: {name}
                    </span>
                  </div>
                  <div className="text-xs text-gray-800">Time taken: {timeTaken}</div>
                </div>

                {isExpanded && (
                  <div className="p-3 bg-white rounded-b-lg w-full">
                    <pre className="text-sm bg-gray-50 p-2 rounded whitespace-pre-wrap break-all">
                      {JSON.stringify(stepValueWithoutName, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-sm text-gray-500">
            No tracer data available.
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
