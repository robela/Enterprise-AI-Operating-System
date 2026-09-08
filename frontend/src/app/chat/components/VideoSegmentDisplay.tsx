"use client";

import React, { useRef } from "react";
import { ChatVideoSegment } from "../types";

interface VideoSegmentDisplayProps {
  segment: ChatVideoSegment;
}

const formatTimestamp = (totalSeconds: number): string => {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
};

/**
 * Inline player for a single retrieved video segment. Uses native HTML5
 * `<video>` plus a W3C Media Fragments `#t=start,end` to seek to the
 * starting offset. We enforce the end bound ourselves: the fragment alone
 * doesn't pause at `end`, so `onTimeUpdate` does it. `onSeeking` rearms the
 * auto-pause so scrubbing back works as expected — but if the user resumes
 * past `end` after the first auto-pause, we leave them alone.
 */
export default function VideoSegmentDisplay({
  segment,
}: VideoSegmentDisplayProps) {
  const hasAutoPausedRef = useRef(false);

  return (
    <div className="relative">
      <video
        controls
        preload="metadata"
        src={`${segment.source_url}#t=${segment.start_sec},${segment.end_sec}`}
        onTimeUpdate={(event) => {
          if (
            !hasAutoPausedRef.current &&
            event.currentTarget.currentTime >= segment.end_sec
          ) {
            event.currentTarget.pause();
            hasAutoPausedRef.current = true;
          }
        }}
        onSeeking={() => {
          hasAutoPausedRef.current = false;
        }}
        className="w-full rounded-lg bg-black"
      />
      <div className="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded">
        <div>{segment.topic}</div>
        <div className="mt-1 text-gray-500">
          {segment.title} — {formatTimestamp(segment.start_sec)} to{" "}
          {formatTimestamp(segment.end_sec)}
        </div>
      </div>
    </div>
  );
}
