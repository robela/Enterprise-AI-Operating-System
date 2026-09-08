"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 font-mono text-sm">
      <h2 className="text-red-600 font-bold text-lg mb-4">Error</h2>
      <pre className="bg-gray-100 p-4 rounded max-w-2xl w-full overflow-auto text-red-700 whitespace-pre-wrap">
        {error.message}
        {error.digest && `\n\nDigest: ${error.digest}`}
        {error.stack && `\n\nStack:\n${error.stack}`}
      </pre>
      <button
        onClick={reset}
        className="mt-6 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Try again
      </button>
    </div>
  );
}
