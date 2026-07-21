import React from "react";

/**
 * Generic elevated surface for roadmap steps and panels.
 */
export default function Card({ children, className = "" }) {
  return (
    <div
      className={`rounded-2xl border border-slate-700/60 bg-surface-card/90 p-6 shadow-glow backdrop-blur ${className}`}
    >
      {children}
    </div>
  );
}
