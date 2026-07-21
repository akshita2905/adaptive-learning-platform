import React, { useState } from "react";
import Card from "./Card.jsx";

/**
 * Roadmap phase with AI detail, YouTube thumbnails, curated courses, and feedback toggles.
 */
export default function RoadmapStepCard({
  phase,
  index,
  videos = [],
  courses = [],
  aiDetail = null,
  generationId,
  stepStatus,
  onFeedback,
  onClearStep,
  feedbackPending,
}) {
  const days = `${phase.days_start}–${phase.days_end}`;
  const explanation = aiDetail?.explanation || "";
  const tasks = Array.isArray(aiDetail?.tasks) ? aiDetail.tasks : [];
  const tips = Array.isArray(aiDetail?.learning_tips) ? aiDetail.learning_tips : [];
  const title = aiDetail?.title || phase.phase;

  const [localError, setLocalError] = useState("");

  const send = async (status) => {
    setLocalError("");
    try {
      await onFeedback?.({
        step_index: index,
        phase_name: phase.phase,
        status,
        generation_id: generationId || null,
      });
    } catch (e) {
      setLocalError(e?.message || "Could not save feedback");
    }
  };

  return (
    <Card className="relative flex flex-col overflow-hidden">
      <div className="absolute right-4 top-4 font-display text-5xl font-bold text-slate-800/80">{index + 1}</div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-brand-500">Day {days}</p>
      <h3 className="mb-2 font-display text-xl font-semibold text-white">{title}</h3>
      <p className="mb-3 text-sm leading-relaxed text-slate-400">{phase.topics}</p>

      {explanation && (
        <div className="mb-4 rounded-xl border border-brand-500/20 bg-brand-500/5 p-3 text-sm text-slate-200">
          <span className="text-xs font-semibold uppercase text-brand-400">AI explanation</span>
          <p className="mt-1 leading-relaxed text-slate-300">{explanation}</p>
        </div>
      )}

      {tasks.length > 0 && (
        <ul className="mb-3 list-inside list-disc text-sm text-slate-400">
          {tasks.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      )}

      {tips.length > 0 && (
        <div className="mb-4 text-xs text-amber-200/90">
          <span className="font-semibold text-amber-400">Tips: </span>
          {tips.join(" · ")}
        </div>
      )}

      {videos.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Videos</p>
          <div className="flex flex-wrap gap-3">
            {videos.map((v) => (
              <a
                key={v.url}
                href={v.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group w-[140px] shrink-0"
              >
                {v.thumbnail ? (
                  <img
                    src={v.thumbnail}
                    alt=""
                    className="mb-1 h-[78px] w-full rounded-lg object-cover ring-1 ring-slate-700 transition group-hover:ring-brand-500/50"
                  />
                ) : (
                  <div className="mb-1 flex h-[78px] items-center justify-center rounded-lg bg-slate-800 text-xs text-slate-500">
                    Play
                  </div>
                )}
                <p className="line-clamp-2 text-xs text-slate-400 group-hover:text-brand-300">{v.title}</p>
              </a>
            ))}
          </div>
        </div>
      )}

      {courses.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Courses</p>
          <ul className="space-y-1 text-sm text-slate-400">
            {courses.map((c) => (
              <li key={c} className="flex gap-2">
                <span className="text-emerald-500">◆</span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-auto flex flex-wrap gap-2 border-t border-slate-700/60 pt-4">
        <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={stepStatus === "completed"}
            disabled={feedbackPending}
            onChange={(e) => {
              if (e.target.checked) send("completed");
              else if (stepStatus === "completed") onClearStep?.(index);
            }}
            className="rounded border-slate-600 bg-slate-800 text-emerald-500"
          />
          Completed
        </label>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={stepStatus === "not_understood"}
            disabled={feedbackPending}
            onChange={(e) => {
              if (e.target.checked) send("not_understood");
              else if (stepStatus === "not_understood") onClearStep?.(index);
            }}
            className="rounded border-slate-600 bg-slate-800 text-amber-500"
          />
          Not understood
        </label>
      </div>
      {localError && <p className="mt-2 text-xs text-red-400">{localError}</p>}
    </Card>
  );
}
