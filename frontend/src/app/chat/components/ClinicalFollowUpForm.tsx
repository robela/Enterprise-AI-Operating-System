"use client";

import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ClinicalFollowUpFormProps {
  missingFields: string[];
  disabled: boolean;
  onSubmit: (text: string) => void;
}

const labels: Record<string, string> = {
  child_age: "Child's age (years)",
  general_danger_signs: "General danger signs",
  main_symptoms: "Main symptoms",
  nutrition_status: "Nutrition or feeding status",
  immunization_status: "Immunization status",
  other_problems: "Other problems",
  // Built-in danger-sign checklist. The backend routes answers by these labels.
  other_danger_signs: "Other danger signs",
  symptom_assessment: "Cough, diarrhoea, malnutrition, ear problems",
  child_weight: "Child's weight (kg)",
};

const wideFields = new Set(["main_symptoms", "nutrition_status", "other_problems", "symptom_assessment"]);

const selectOptions: Record<string, string[]> = {
  general_danger_signs: ["No danger signs", "Danger signs present", "Not known"],
  other_danger_signs: ["No other danger signs", "Other danger signs present", "Not known"],
  immunization_status: ["Up to date", "Not up to date", "Not known"],
};

export default function ClinicalFollowUpForm({ missingFields, disabled, onSubmit }: ClinicalFollowUpFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const answers = missingFields
      .filter((field) => values[field]?.trim())
      .map((field) => `${labels[field] || field}: ${values[field]}`);
    if (answers.length > 0) onSubmit(answers.join(". "));
  };

  return (
    <form onSubmit={submit} className="mt-4 border-t pt-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {missingFields.map((field) => (
          <label key={field} className={wideFields.has(field) ? "sm:col-span-2" : ""}>
            <span className="mb-1 block text-sm font-medium">{labels[field] || field.replaceAll("_", " ")}</span>
            {field === "child_weight" ? (
              <Input
                aria-label={labels[field]}
                type="number"
                min="0"
                max="100"
                step="0.1"
                inputMode="decimal"
                value={values[field] || ""}
                onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))}
                disabled={disabled}
              />
            ) : field === "child_age" ? (
              <Input
                aria-label={labels[field]}
                type="number"
                min="0"
                max="18"
                inputMode="numeric"
                value={values[field] || ""}
                onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))}
                disabled={disabled}
              />
            ) : selectOptions[field] ? (
              <Select value={values[field] || ""} onValueChange={(value) => setValues((current) => ({ ...current, [field]: value }))} disabled={disabled}>
                <SelectTrigger aria-label={labels[field]}><SelectValue placeholder="Select status" /></SelectTrigger>
                <SelectContent>
                  {selectOptions[field].map((option) => <SelectItem key={option} value={option}>{option}</SelectItem>)}
                </SelectContent>
              </Select>
            ) : (
              <Textarea
                aria-label={labels[field]}
                value={values[field] || ""}
                onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))}
                disabled={disabled}
                rows={2}
                className="resize-y"
              />
            )}
          </label>
        ))}
      </div>
      <div className="mt-3 flex justify-end">
        <Button type="submit" size="sm" disabled={disabled || !missingFields.some((field) => values[field]?.trim())}>
          Submit details
        </Button>
      </div>
    </form>
  );
}