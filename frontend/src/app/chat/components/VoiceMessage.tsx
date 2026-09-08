'use client';

import { useEffect, useRef, useState } from 'react';
import { Play, Pause } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceMessageProps {
  audioUrl: string;
  duration?: number;
  isSender?: boolean;
  senderName?: string;
}

export function VoiceMessage({
  audioUrl,
  duration = 45,
  isSender = false,
  senderName,
}: VoiceMessageProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setTotalDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = totalDuration ? (currentTime / totalDuration) * 100 : 0;

  // Generate waveform bars
  const waveformBars = Array.from({ length: 12 }, (_, i) => {
    const base = 40 + Math.sin(i * 0.5) * 20;
    const factor = isPlaying ? (currentTime / totalDuration) * (i + 1) : i * 5;
    const height = base + Math.sin(factor) * 20;
    return Math.max(8, Math.min(100, height));
  });

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-2xl max-w-xs',
        isSender
          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
          : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
      )}
    >
      <audio ref={audioRef} src={audioUrl} />

      {/* Play/Pause Button */}
      <button
        onClick={togglePlayPause}
        className={cn(
          'flex-shrink-0 flex items-center justify-center rounded-full p-2 transition-all',
          isSender
            ? 'bg-white/20 hover:bg-white/30 active:scale-95'
            : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 active:scale-95'
        )}
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? (
          <Pause
            size={18}
            className={isSender ? 'text-white' : 'text-gray-700 dark:text-gray-300'}
            fill="currentColor"
          />
        ) : (
          <Play
            size={18}
            className={isSender ? 'text-white' : 'text-gray-700 dark:text-gray-300'}
            fill="currentColor"
          />
        )}
      </button>

      {/* Waveform Visualization */}
      <div className="flex items-center justify-center gap-0.5 h-8 flex-1">
        {waveformBars.map((height, i) => (
          <div
            key={i}
            className={cn(
              'w-1 rounded-full transition-all duration-100',
              isSender
                ? `${i <= (currentTime / totalDuration) * waveformBars.length ? 'bg-white' : 'bg-white/40'}`
                : `${i <= (currentTime / totalDuration) * waveformBars.length ? 'bg-blue-500 dark:bg-blue-400' : 'bg-gray-300 dark:bg-gray-600'}`
            )}
            style={{ height: `${height}%` }}
          />
        ))}
      </div>

      {/* Time Display */}
      <div
        className={cn(
          'text-xs font-medium flex-shrink-0 tabular-nums',
          isSender ? 'text-white/80' : 'text-gray-600 dark:text-gray-400'
        )}
      >
        {formatTime(currentTime)} / {formatTime(totalDuration)}
      </div>
    </div>
  );
}
