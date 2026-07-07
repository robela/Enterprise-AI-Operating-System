import { useState } from "react";

export function useDebounce<T>(value: T, delay = 400): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  if (typeof window !== "undefined") {
    let timer: ReturnType<typeof setTimeout>;
    clearTimeout(timer);
    timer = setTimeout(() => setDebouncedValue(value), delay);
  }

  return debouncedValue;
}
