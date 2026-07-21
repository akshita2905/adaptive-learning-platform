import React from "react";

/**
 * Full-screen dimmed overlay with spinner while async generation runs.
 */
export default function LoadingOverlay({ visible, message = "Building your personalized roadmap…" }) {
  if (!visible) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/85 backdrop-blur-sm"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="h-14 w-14 animate-spin rounded-full border-4 border-brand-500/30 border-t-brand-500" />
      <p className="mt-6 max-w-sm text-center text-sm text-slate-300">{message}</p>
      <p className="mt-2 text-xs text-slate-500">ML + LLM + YouTube — may take 15–40s</p>
    </div>
  );
}
