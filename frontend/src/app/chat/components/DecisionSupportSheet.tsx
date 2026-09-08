"use client";

import React, { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, CheckCircle2, ChevronLeft, ChevronRight, Loader2, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TagCategoryOut } from "../api";
import {
  DSSelections,
  HewEntry,
  PhcuEntry,
  ProgramOption,
  useDecisionSupport,
} from "../hooks/useDecisionSupport";

type DSHook = ReturnType<typeof useDecisionSupport>;

interface DecisionSupportSheetProps {
  hook: DSHook;
  onComplete: () => void;
}

const LANGUAGES = ["Local", "Amharic", "Oromo", "English"];
const PAGE_SIZE = 20;

// Step number → which DSSelections key indicates it was skipped (null = skipped)
const SKIPPABLE_STEPS: Partial<Record<number, keyof DSSelections>> = {
  1: "hew",
  2: "languagePref",
  5: "program",
  6: "tag",
};

const STEP_TITLES: Record<number, string> = {
  1: "Health Extension Worker",
  2: "Language Preference",
  3: "Action Taken",
  4: "Intent Changed",
  5: "Program",
  6: "Tag",
  7: "Summary",
};

// ─── Sort types ──────────────────────────────────────────────────────────────

type HewSortCol = "name" | "woreda" | "zone" | "phcu";
type TagSortCol = "name" | "category";
type SortDir = "asc" | "desc";

// ─── Shared sub-components ───────────────────────────────────────────────────

function StepIndicator({
  step,
  total,
  selections,
  onStepClick,
}: {
  step: number;
  total: number;
  selections: DSSelections;
  onStepClick: (n: number) => void;
}) {
  const wasSkipped = (n: number): boolean => {
    if (n >= step) return false;
    const key = SKIPPABLE_STEPS[n];
    return key ? selections[key] === null : false;
  };

  return (
    <div className="flex items-center w-full">
      {Array.from({ length: total }, (_, i) => {
        const n = i + 1;
        const isPast = n < step;
        const isActive = n === step;
        const skipped = wasSkipped(n);
        return (
          <React.Fragment key={n}>
            <button
              type="button"
              onClick={() => onStepClick(n)}
              aria-label={`Go to step ${n}: ${STEP_TITLES[n]}`}
              aria-current={isActive ? "step" : undefined}
              className={`flex items-center justify-center rounded-full text-[10px] font-bold shrink-0 transition-all duration-200 cursor-pointer hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 ${
                isActive
                  ? "h-6 w-6 bg-gray-900 text-white ring-2 ring-gray-900 ring-offset-2"
                  : isPast && skipped
                  ? "h-5 w-5 bg-amber-100 text-amber-400 border border-amber-300"
                  : isPast
                  ? "h-6 w-6 bg-green-500 text-white"
                  : "h-5 w-5 bg-gray-100 text-gray-300 border border-gray-200"
              }`}
            >
              {isPast && !skipped ? "✓" : isPast && skipped ? "–" : n}
            </button>
            {n < total && (
              <div
                className={`flex-1 h-0.5 mx-1 transition-colors duration-200 ${
                  isPast && skipped
                    ? "bg-amber-200"
                    : isPast
                    ? "bg-green-400"
                    : "bg-gray-200"
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function OptionCard({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-xl border-2 px-4 py-3 text-sm font-medium text-left transition-all active:scale-[0.98] ${
        selected
          ? "border-gray-900 bg-gray-50"
          : "border-gray-200 hover:border-gray-400 hover:bg-gray-50"
      }`}
    >
      {label}
    </button>
  );
}

function SortIcon<T extends string>({
  col,
  sortCol,
  sortDir,
}: {
  col: T;
  sortCol: T;
  sortDir: SortDir;
}) {
  if (col !== sortCol) return <ArrowUpDown className="ml-1 h-3 w-3 text-gray-300 inline" />;
  return sortDir === "asc"
    ? <ArrowUp className="ml-1 h-3 w-3 text-gray-700 inline" />
    : <ArrowDown className="ml-1 h-3 w-3 text-gray-700 inline" />;
}

function SelectedBanner({
  label,
  sublabel,
  onClear,
  onContinue,
}: {
  label: string;
  sublabel?: string;
  onClear: () => void;
  onContinue: () => void;
}) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2.5 shrink-0 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-green-700 truncate">{label}</p>
            {sublabel && <p className="text-xs text-green-500 truncate">{sublabel}</p>}
          </div>
        </div>
        <button
          onClick={onClear}
          className="p-1 rounded hover:bg-green-100 transition-colors shrink-0"
          title="Clear selection"
          aria-label="Clear selection"
        >
          <X className="h-3.5 w-3.5 text-green-500" />
        </button>
      </div>
      <button
        onClick={onContinue}
        className="w-full rounded-md bg-green-600 hover:bg-green-700 active:bg-green-800 text-white text-xs font-medium py-1.5 transition-colors"
      >
        Continue with this selection →
      </button>
    </div>
  );
}

function Pagination({
  page,
  totalPages,
  total,
  onPrev,
  onNext,
}: {
  page: number;
  totalPages: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex items-center justify-between text-xs text-gray-500 shrink-0">
      <span>
        Page {page} of {totalPages} &nbsp;·&nbsp; {total} results
      </span>
      <div className="flex gap-1">
        <Button
          size="sm"
          variant="outline"
          className="h-7 w-7 p-0"
          disabled={page === 1}
          onClick={onPrev}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="h-7 w-7 p-0"
          disabled={page === totalPages}
          onClick={onNext}
          aria-label="Next page"
        >
          <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ─── Step components ──────────────────────────────────────────────────────────

function StepHew({
  hews,
  phcus,
  selected,
  onRowClick,
  onSkip,
  onContinue,
}: {
  hews: HewEntry[];
  phcus: PhcuEntry[];
  selected: { id: string; name: string; woreda: string } | null;
  onRowClick: (hew: { id: string; name: string; woreda: string } | null) => void;
  onSkip: () => void;
  onContinue: () => void;
}) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sortCol, setSortCol] = useState<HewSortCol>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const phcuMap = useMemo(
    () => Object.fromEntries(phcus.map((p) => [p.id, p.name])),
    [phcus]
  );

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    const results = q
      ? hews.filter(
          (h) =>
            h.name.toLowerCase().includes(q) ||
            h.woreda.toLowerCase().includes(q) ||
            h.zone.toLowerCase().includes(q) ||
            (phcuMap[h.phcuId] ?? "").toLowerCase().includes(q)
        )
      : [...hews];

    results.sort((a, b) => {
      const vals: Record<HewSortCol, [string, string]> = {
        name:   [a.name,               b.name],
        woreda: [a.woreda,             b.woreda],
        zone:   [a.zone,               b.zone],
        phcu:   [phcuMap[a.phcuId] ?? "", phcuMap[b.phcuId] ?? ""],
      };
      const [valA, valB] = vals[sortCol];
      return sortDir === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    return results;
  }, [hews, search, phcuMap, sortCol, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleSort = (col: HewSortCol) => {
    if (col === sortCol) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortCol(col); setSortDir("asc"); }
    setPage(1);
  };

  const handleSearch = (v: string) => { setSearch(v); setPage(1); };

  return (
    <div className="flex flex-col gap-3 flex-1 min-h-0">
      <p className="text-sm font-medium text-gray-700 shrink-0">Select the Health Extension Worker</p>

      {selected && (
        <SelectedBanner
          label={selected.name}
          sublabel={selected.woreda}
          onClear={() => onRowClick(null)}
          onContinue={onContinue}
        />
      )}

      <div className="flex gap-2 items-center shrink-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search name, woreda, zone or PHCU..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <button
          onClick={onSkip}
          className="text-xs text-gray-400 hover:text-gray-600 underline underline-offset-2 transition-colors whitespace-nowrap shrink-0"
        >
          Skip
        </button>
      </div>

      <div className="flex-1 min-h-0 rounded-lg border border-gray-200 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200">
            <tr>
              {(["name", "woreda", "zone", "phcu"] as HewSortCol[]).map((col, i) => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleSort(col); } }}
                  tabIndex={0}
                  aria-sort={sortCol === col ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
                  className={`h-10 px-3 text-left text-xs font-semibold text-gray-600 cursor-pointer select-none hover:text-gray-900 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500${i >= 2 ? " hidden sm:table-cell" : ""}`}
                >
                  {col.charAt(0).toUpperCase() + col.slice(1)}
                  <SortIcon col={col} sortCol={sortCol} sortDir={sortDir} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center text-sm text-gray-400 py-8">No HEWs found</td>
              </tr>
            ) : (
              paginated.map((h) => {
                const isSelected = selected?.id === h.id;
                return (
                  <tr
                    key={h.id}
                    onClick={() => onRowClick({ id: h.id, name: h.name, woreda: h.woreda })}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick({ id: h.id, name: h.name, woreda: h.woreda }); } }}
                    tabIndex={0}
                    role="row"
                    aria-selected={isSelected}
                    className={`cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 ${isSelected ? "bg-blue-50 hover:bg-blue-100" : "hover:bg-gray-50 active:bg-gray-100"}`}
                  >
                    <td className={`px-3 py-3 text-sm font-medium ${isSelected ? "text-blue-700" : "text-gray-800"}`}>{h.name}</td>
                    <td className={`px-3 py-3 text-sm ${isSelected ? "text-blue-600" : "text-gray-600"}`}>{h.woreda}</td>
                    <td className={`px-3 py-3 text-sm hidden sm:table-cell ${isSelected ? "text-blue-600" : "text-gray-600"}`}>{h.zone}</td>
                    <td className={`px-3 py-3 text-sm hidden sm:table-cell ${isSelected ? "text-blue-600" : "text-gray-600"}`}>{phcuMap[h.phcuId] ?? "—"}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        totalPages={totalPages}
        total={filtered.length}
        onPrev={() => setPage((p) => p - 1)}
        onNext={() => setPage((p) => p + 1)}
      />
    </div>
  );
}

function StepLanguage({
  selected,
  onSelect,
}: {
  selected: string | null;
  onSelect: (lang: string | null) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-gray-700">Select language preference</p>
      <div className="grid grid-cols-2 gap-2">
        {LANGUAGES.map((lang) => (
          <OptionCard
            key={lang}
            label={lang}
            selected={selected === lang}
            onClick={() => onSelect(lang)}
          />
        ))}
      </div>
      <button
        onClick={() => onSelect(null)}
        className="w-full rounded-xl border-2 border-dashed border-gray-200 px-4 py-2.5 text-sm text-gray-400 hover:border-gray-400 hover:text-gray-600 transition-all"
      >
        Skip this step
      </button>
    </div>
  );
}

function StepActionTaken({
  selected,
  onSelect,
}: {
  selected: "managed" | "referred" | null;
  onSelect: (v: "managed" | "referred") => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-gray-700">
        Following this consultation, what is your final decision?
      </p>
      <div className="grid grid-cols-2 gap-3">
        <OptionCard label="Managed" selected={selected === "managed"} onClick={() => onSelect("managed")} />
        <OptionCard label="Referred" selected={selected === "referred"} onClick={() => onSelect("referred")} />
      </div>
    </div>
  );
}

function StepIntentChanged({
  selected,
  onSelect,
}: {
  selected: boolean | null;
  onSelect: (v: boolean) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium text-gray-700">
        Did this consultation change your initial intent?
      </p>
      <div className="grid grid-cols-2 gap-3">
        <OptionCard label="Yes" selected={selected === true} onClick={() => onSelect(true)} />
        <OptionCard label="No" selected={selected === false} onClick={() => onSelect(false)} />
      </div>
    </div>
  );
}

function StepProgram({
  programs,
  selected,
  onRowClick,
  onSkip,
  onContinue,
}: {
  programs: ProgramOption[];
  selected: { id: number | string; name: string } | null;
  onRowClick: (p: { id: number | string; name: string } | null) => void;
  onSkip: () => void;
  onContinue: () => void;
}) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    const results = q
      ? programs.filter((p) => p.name.toLowerCase().includes(q))
      : [...programs];
    results.sort((a, b) =>
      sortDir === "asc" ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name)
    );
    return results;
  }, [programs, search, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleSearch = (v: string) => { setSearch(v); setPage(1); };

  return (
    <div className="flex flex-col gap-3 flex-1 min-h-0">
      <p className="text-sm font-medium text-gray-700">Select a program</p>

      {selected && (
        <SelectedBanner
          label={selected.name}
          onClear={() => onRowClick(null)}
          onContinue={onContinue}
        />
      )}

      <div className="flex gap-2 items-center shrink-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search programs..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <button
          onClick={onSkip}
          className="text-xs text-gray-400 hover:text-gray-600 underline underline-offset-2 transition-colors whitespace-nowrap shrink-0"
        >
          Skip
        </button>
      </div>

      <p className="text-xs text-gray-400 shrink-0">
        {filtered.length} program{filtered.length !== 1 ? "s" : ""}{search ? " found" : " total"}
      </p>

      <div className="flex-1 min-h-0 rounded-lg border border-gray-200 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200">
            <tr>
              <th
                onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSortDir((d) => (d === "asc" ? "desc" : "asc")); } }}
                tabIndex={0}
                aria-sort={sortDir === "asc" ? "ascending" : "descending"}
                className="h-10 px-3 text-left text-xs font-semibold text-gray-600 cursor-pointer select-none hover:text-gray-900 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
              >
                Name
                <SortIcon col="name" sortCol="name" sortDir={sortDir} />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {paginated.length === 0 ? (
              <tr>
                <td className="text-center text-sm text-gray-400 py-8">No programs found</td>
              </tr>
            ) : (
              paginated.map((p) => {
                const isSelected = String(selected?.id) === String(p.program_id);
                return (
                  <tr
                    key={p.program_id}
                    onClick={() => onRowClick({ id: p.program_id, name: p.name })}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick({ id: p.program_id, name: p.name }); } }}
                    tabIndex={0}
                    role="row"
                    aria-selected={isSelected}
                    className={`cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 ${isSelected ? "bg-blue-50 hover:bg-blue-100" : "hover:bg-gray-50 active:bg-gray-100"}`}
                  >
                    <td className={`px-3 py-3 text-sm font-medium ${isSelected ? "text-blue-700" : "text-gray-800"}`}>{p.name}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        totalPages={totalPages}
        total={filtered.length}
        onPrev={() => setPage((p) => p - 1)}
        onNext={() => setPage((p) => p + 1)}
      />
    </div>
  );
}

function StepTag({
  categories,
  selected,
  onRowClick,
  onSkip,
  onContinue,
}: {
  categories: TagCategoryOut[];
  selected: { id: number; name: string } | null;
  onRowClick: (t: { id: number; name: string } | null) => void;
  onSkip: () => void;
  onContinue: () => void;
}) {
  const [search, setSearch] = useState("");
  const [sortCol, setSortCol] = useState<TagSortCol>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const allTags = useMemo(() =>
    categories.flatMap((cat) =>
      cat.children.map((t) => ({ id: t.tag_id, name: t.name, category: cat.category.name }))
    ), [categories]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    const results = q
      ? allTags.filter(
          (t) => t.name.toLowerCase().includes(q) || t.category.toLowerCase().includes(q)
        )
      : [...allTags];
    results.sort((a, b) => {
      const valA = sortCol === "name" ? a.name : a.category;
      const valB = sortCol === "name" ? b.name : b.category;
      return sortDir === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });
    return results;
  }, [allTags, search, sortCol, sortDir]);

  const handleSort = (col: TagSortCol) => {
    if (col === sortCol) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortCol(col); setSortDir("asc"); }
  };

  return (
    <div className="flex flex-col gap-3 flex-1 min-h-0">
      <p className="text-sm font-medium text-gray-700">Select a tag</p>

      {selected && (
        <SelectedBanner
          label={selected.name}
          sublabel={allTags.find((t) => t.id === selected.id)?.category}
          onClear={() => onRowClick(null)}
          onContinue={onContinue}
        />
      )}

      <div className="flex gap-2 items-center shrink-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by tag name or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <button
          onClick={onSkip}
          className="text-xs text-gray-400 hover:text-gray-600 underline underline-offset-2 transition-colors whitespace-nowrap shrink-0"
        >
          Skip
        </button>
      </div>

      <p className="text-xs text-gray-400 shrink-0">
        {filtered.length} tag{filtered.length !== 1 ? "s" : ""}{search ? " found" : " total"}
      </p>

      <div className="flex-1 min-h-0 rounded-lg border border-gray-200 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200">
            <tr>
              {(["name", "category"] as TagSortCol[]).map((col) => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleSort(col); } }}
                  tabIndex={0}
                  aria-sort={sortCol === col ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
                  className="h-10 px-3 text-left text-xs font-semibold text-gray-600 cursor-pointer select-none hover:text-gray-900 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
                >
                  {col.charAt(0).toUpperCase() + col.slice(1)}
                  <SortIcon col={col} sortCol={sortCol} sortDir={sortDir} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={2} className="text-center text-sm text-gray-400 py-8">No tags found</td>
              </tr>
            ) : (
              filtered.map((t) => {
                const isSelected = selected?.id === t.id;
                return (
                  <tr
                    key={t.id}
                    onClick={() => onRowClick({ id: t.id, name: t.name })}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRowClick({ id: t.id, name: t.name }); } }}
                    tabIndex={0}
                    role="row"
                    aria-selected={isSelected}
                    className={`cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 ${isSelected ? "bg-blue-50 hover:bg-blue-100" : "hover:bg-gray-50 active:bg-gray-100"}`}
                  >
                    <td className={`px-3 py-3 text-sm font-medium ${isSelected ? "text-blue-700" : "text-gray-800"}`}>{t.name}</td>
                    <td className={`px-3 py-3 text-sm ${isSelected ? "text-blue-600" : "text-gray-600"}`}>{t.category}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-xs uppercase tracking-wide text-gray-400 font-medium">{label}</span>
      <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700 max-w-[55%] text-right truncate">
        {value}
      </span>
    </div>
  );
}

function StepSummary({
  selections,
  isSaving,
  onConfirm,
}: {
  selections: DSSelections;
  isSaving: boolean;
  onConfirm: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm font-medium text-gray-700">Review your selections</p>
      <div className="rounded-xl bg-gray-50 px-4 divide-y divide-gray-200">
        <SummaryRow label="HEW" value={selections.hew?.name ?? "—"} />
        <SummaryRow label="Language" value={selections.languagePref ?? "—"} />
        <SummaryRow label="Action Taken" value={selections.actionTaken ?? "—"} />
        <SummaryRow
          label="Intent Changed"
          value={selections.intentChanged === null ? "—" : selections.intentChanged ? "Yes" : "No"}
        />
        <SummaryRow label="Program" value={selections.program?.name ?? "—"} />
        <SummaryRow label="Tag" value={selections.tag?.name ?? "—"} />
      </div>
      <Button onClick={onConfirm} disabled={isSaving} className="w-full">
        {isSaving ? (
          <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</>
        ) : (
          <><CheckCircle2 className="mr-2 h-4 w-4" />Confirm & Save</>
        )}
      </Button>
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────────────

export default function DecisionSupportSheet({
  hook,
  onComplete,
}: DecisionSupportSheetProps) {
  const showBack = hook.step > 1 && !hook.isSaving;

  return (
    <div className="flex flex-col h-[75vh]">
      <div className="px-5 pt-1 pb-3 border-b shrink-0">
        <div className="flex items-center gap-2">
          {showBack && (
            <button
              onClick={hook.goBack}
              aria-label="Go back"
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <ChevronLeft className="h-4 w-4 text-gray-500" />
            </button>
          )}
          <h2 className="text-base font-semibold">Decision Support</h2>
        </div>
        <p className="text-xs text-gray-500 font-normal">{STEP_TITLES[hook.step]}</p>
        <div className="pt-2">
          <StepIndicator step={hook.step} total={hook.totalSteps} selections={hook.selections} onStepClick={hook.goToStep} />
        </div>
      </div>

      <div className="flex-1 min-h-0 px-5 py-4 flex flex-col overflow-hidden">
            {hook.isLoadingData ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <>
                {hook.step === 1 && (
                  <StepHew
                    hews={hook.contextOptions?.hews ?? []}
                    phcus={hook.contextOptions?.phcus ?? []}
                    selected={hook.selections.hew}
                    onRowClick={hook.setHewOnly}
                    onSkip={hook.skipHew}
                    onContinue={() => hook.goToStep(2)}
                  />
                )}
                {hook.step === 2 && (
                  <div className="overflow-y-auto flex-1">
                    <StepLanguage
                      selected={hook.selections.languagePref}
                      onSelect={hook.selectLanguage}
                    />
                  </div>
                )}
                {hook.step === 3 && (
                  <div className="overflow-y-auto flex-1">
                    <StepActionTaken
                      selected={hook.selections.actionTaken}
                      onSelect={hook.selectActionTaken}
                    />
                  </div>
                )}
                {hook.step === 4 && (
                  <div className="overflow-y-auto flex-1">
                    <StepIntentChanged
                      selected={hook.selections.intentChanged}
                      onSelect={hook.selectIntentChanged}
                    />
                  </div>
                )}
                {hook.step === 5 && (
                  <StepProgram
                    programs={hook.programs}
                    selected={hook.selections.program}
                    onRowClick={hook.setProgramOnly}
                    onSkip={hook.skipProgram}
                    onContinue={() => hook.goToStep(6)}
                  />
                )}
                {hook.step === 6 && (
                  hook.groupedTags ? (
                    <StepTag
                      categories={hook.groupedTags.categories}
                      selected={hook.selections.tag}
                      onRowClick={hook.setTagOnly}
                      onSkip={hook.skipTag}
                      onContinue={() => hook.goToStep(7)}
                    />
                  ) : (
                    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-10 text-center">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                      <div className="space-y-2">
                        <p className="font-medium">Tags are not available yet</p>
                        <p className="text-sm text-muted-foreground">
                          We are still loading tag options, or they could not be retrieved.
                          Please go back and try again.
                        </p>
                      </div>
                      <Button type="button" variant="outline" onClick={() => hook.goToStep(5)}>
                        Back to program selection
                      </Button>
                    </div>
                  )
                )}
                {hook.step === 7 && (
                  <div className="overflow-y-auto flex-1">
                    <StepSummary
                      selections={hook.selections}
                      isSaving={hook.isSaving}
                      onConfirm={() => hook.handleSubmit(onComplete)}
                    />
                  </div>
                )}
              </>
            )}
      </div>
    </div>
  );
}
