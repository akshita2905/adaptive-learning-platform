import React, { useCallback, useEffect, useMemo, useState } from "react";
import api from "../api/client.js";
import Card from "../components/Card.jsx";
import Layout from "../components/Layout.jsx";
import LoadingOverlay from "../components/LoadingOverlay.jsx";
import RoadmapStepCard from "../components/RoadmapStepCard.jsx";
import SkillPicker from "../components/SkillPicker.jsx";
import { getPhases, normalizePathResult } from "../utils/normalizeResult.js";

const GOALS = [
  "Data Scientist",
  "Web Developer",
  "ML Engineer",
  "DevOps Engineer",
  "Mobile Developer",
  "Data Analyst",
  "Backend Engineer",
  "Frontend Engineer",
  "Security Engineer",
];

/**
 * Build latest status + feedback id per step for the active generation.
 */
function feedbackIndexForGeneration(feedbackList, generationId) {
  if (!generationId) return {};
  const rows = feedbackList.filter((f) => f.generation_id === generationId);
  rows.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const map = {};
  for (const f of rows) {
    map[f.step_index] = { id: f.id, status: f.status };
  }
  return map;
}

/**
 * Curated courses whose topic keyword appears in the phase text.
 */
function coursesForPhase(phase, coursesMap) {
  if (!coursesMap || !phase) return [];
  const blob = `${phase.phase || ""} ${phase.topics || ""}`.toLowerCase();
  const out = [];
  for (const [topic, list] of Object.entries(coursesMap)) {
    if (topic.toLowerCase() && blob.includes(topic.toLowerCase())) {
      out.push(...list);
    }
  }
  return [...new Set(out)];
}

function priorityBadgeClass(priority) {
  if (priority === "HIGH") return "bg-red-500/20 text-red-300 border-red-500/40";
  if (priority === "MEDIUM") return "bg-amber-500/15 text-amber-200 border-amber-500/35";
  return "bg-slate-600/30 text-slate-300 border-slate-600/50";
}

/**
 * Dashboard: advanced path (ML + LLM + YouTube), progress, feedback, regenerate.
 */
export default function DashboardPage() {
  const [skills, setSkills] = useState(["Python"]);
  const [goal, setGoal] = useState(GOALS[0]);
  const [experienceLevel, setExperienceLevel] = useState("Intermediate");
  const [inferLevel, setInferLevel] = useState(false);
  const [hoursPerDay, setHoursPerDay] = useState(2);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [feedbackList, setFeedbackList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [feedbackPending, setFeedbackPending] = useState(false);
  const [error, setError] = useState("");
  const [histError, setHistError] = useState("");

  const norm = useMemo(() => normalizePathResult(result), [result]);
  const phases = useMemo(() => getPhases(result), [result]);
  const fbByStep = useMemo(
    () => feedbackIndexForGeneration(feedbackList, norm?.generation_id),
    [feedbackList, norm?.generation_id]
  );

  const completedCount = useMemo(() => {
    return Object.values(fbByStep).filter((x) => x.status === "completed").length;
  }, [fbByStep]);
  const progressPct = phases.length ? Math.round((completedCount / phases.length) * 100) : 0;

  const loadHistory = async () => {
    setHistError("");
    try {
      const { data } = await api.get("/history");
      setHistory(data);
    } catch (err) {
      setHistError(err.response?.data?.detail || "Could not load history");
    }
  };

  const loadFeedback = async () => {
    try {
      const { data } = await api.get("/feedback");
      setFeedbackList(data);
    } catch {
      /* optional */
    }
  };

  useEffect(() => {
    loadHistory();
    loadFeedback();
  }, []);

  const runGenerate = async (regenerateSmarter) => {
    setError("");
    setLoading(true);
    if (!regenerateSmarter) setResult(null);
    try {
      const body = {
        skills,
        goal,
        hours_per_day: Number(hoursPerDay),
        experience_level: inferLevel ? null : experienceLevel,
        regenerate_smarter: regenerateSmarter,
        use_cache: !regenerateSmarter,
      };
      const { data } = await api.post("/generate-path", body);
      setResult(data);
      await loadHistory();
      await loadFeedback();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Generation failed";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const onGenerate = (e) => {
    e.preventDefault();
    runGenerate(false);
  };

  const onFeedback = useCallback(
    async (payload) => {
      setFeedbackPending(true);
      try {
        await api.post("/feedback", payload);
        await loadFeedback();
      } finally {
        setFeedbackPending(false);
      }
    },
    []
  );

  const clearStepFeedback = useCallback(
    async (stepIndex) => {
      const meta = fbByStep[stepIndex];
      if (!meta?.id) return;
      setFeedbackPending(true);
      try {
        await api.delete(`/feedback/${meta.id}`);
        await loadFeedback();
      } finally {
        setFeedbackPending(false);
      }
    },
    [fbByStep]
  );

  const detailedPlan = norm?.ai_roadmap?.detailed_plan || [];
  const bp = norm?.base_path || {};

  return (
    <Layout title="Your learning dashboard">
      <LoadingOverlay visible={loading} />

      <div className="grid gap-10 lg:grid-cols-[1fr_320px]">
        <div className="space-y-8">
          <Card>
            <h2 className="font-display mb-2 text-xl font-semibold text-white">Build a path</h2>
            <p className="mb-6 text-sm text-slate-400">
              ML selects a catalog match; OpenAI expands it into day-wise guidance; YouTube and curated
              courses attach per phase. Mark steps to adapt your next generation.
            </p>
            <form onSubmit={onGenerate} className="space-y-6">
              {error && (
                <p className="rounded-lg border border-red-500/40 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                  {error}
                </p>
              )}
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-300">Skills</label>
                <SkillPicker value={skills} onChange={setSkills} />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm text-slate-400">Goal</label>
                  <select
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    className="w-full rounded-xl border border-slate-600 bg-slate-900/80 px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {GOALS.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-400">Hours per day</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="12"
                    value={hoursPerDay}
                    onChange={(e) => setHoursPerDay(e.target.value)}
                    className="w-full rounded-xl border border-slate-600 bg-slate-900/80 px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={inferLevel}
                    onChange={(e) => setInferLevel(e.target.checked)}
                    className="rounded border-slate-600 bg-slate-800 text-brand-600"
                  />
                  Infer experience level with ML
                </label>
              </div>
              {!inferLevel && (
                <div>
                  <label className="mb-1 block text-sm text-slate-400">Experience</label>
                  <select
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value)}
                    className="w-full max-w-xs rounded-xl border border-slate-600 bg-slate-900/80 px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                  </select>
                </div>
              )}
              <div className="flex flex-wrap gap-3">
                <button
                  type="submit"
                  disabled={loading || skills.length === 0}
                  className="rounded-xl bg-brand-600 px-8 py-3 font-semibold text-white shadow-glow transition hover:bg-brand-500 disabled:opacity-50"
                >
                  {loading ? "Generating…" : "Generate learning path"}
                </button>
                <button
                  type="button"
                  disabled={loading || skills.length === 0}
                  onClick={() => runGenerate(true)}
                  className="rounded-xl border border-violet-500/50 bg-violet-500/10 px-6 py-3 font-semibold text-violet-200 transition hover:bg-violet-500/20 disabled:opacity-50"
                >
                  Regenerate smarter path
                </button>
              </div>
            </form>
          </Card>

          {norm && (
            <div className="space-y-6">
              {phases.length > 0 && (
                <Card>
                  <div className="mb-2 flex items-center justify-between gap-4">
                    <h3 className="font-semibold text-white">Progress</h3>
                    <span className="text-sm text-slate-400">
                      {completedCount}/{phases.length} steps
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-brand-600 to-emerald-500 transition-all duration-500"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Check &quot;Completed&quot; on steps you finish — your next roadmap extends topics you
                    mark as not understood.
                  </p>
                </Card>
              )}

              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="font-display text-2xl font-bold text-white">{bp.matched_role}</h2>
                  <p className="text-slate-400">
                    ~{bp.timeline_days} days ({bp.timeline_weeks} weeks) · similarity{" "}
                    {(bp.similarity_score ?? 0).toFixed(3)}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-700 bg-slate-800/50 px-4 py-2 text-sm text-slate-300">
                  Level: <strong className="text-white">{bp.experience_level_used}</strong>
                  {bp.predicted_level && (
                    <span className="text-slate-500"> (predicted: {bp.predicted_level})</span>
                  )}
                </div>
              </div>

              <Card>
                <h3 className="mb-2 font-semibold text-white">Overview</h3>
                <p className="text-slate-400">{bp.summary}</p>
                <p className="mt-4 text-sm leading-relaxed text-slate-300">{bp.ai_explanation}</p>
              </Card>

              {(norm.ai_roadmap?.explanations || norm.ai_roadmap?.tips?.length > 0) && (
                <Card>
                  <h3 className="mb-2 font-semibold text-white">AI coach</h3>
                  {norm.ai_roadmap.explanations && (
                    <p className="text-sm leading-relaxed text-slate-300">{norm.ai_roadmap.explanations}</p>
                  )}
                  {norm.ai_roadmap.tips?.length > 0 && (
                    <ul className="mt-3 list-inside list-disc text-sm text-slate-400">
                      {norm.ai_roadmap.tips.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  )}
                </Card>
              )}

              {norm.skill_gaps?.length > 0 && (
                <Card>
                  <h3 className="mb-3 font-semibold text-white">Skill gap analysis</h3>
                  <div className="flex flex-wrap gap-2">
                    {norm.skill_gaps.map((g) => (
                      <span
                        key={g.skill}
                        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${priorityBadgeClass(g.priority)}`}
                      >
                        {g.skill}
                        <span className="opacity-70">
                          {g.priority} · {(g.score ?? 0).toFixed(2)}
                        </span>
                      </span>
                    ))}
                  </div>
                </Card>
              )}

              <div>
                <h3 className="mb-4 font-display text-xl font-semibold text-white">Roadmap</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  {phases.map((phase, i) => {
                    const vids = norm.videos?.[String(i)] || norm.videos?.[i] || [];
                    const aiDetail = detailedPlan[i] || null;
                    const crs = coursesForPhase(phase, norm.courses);
                    const stepMeta = fbByStep[i];
                    const stepStatus = stepMeta?.status || null;
                    return (
                      <RoadmapStepCard
                        key={`${phase.phase}-${i}`}
                        phase={phase}
                        index={i}
                        videos={vids}
                        courses={crs}
                        aiDetail={aiDetail}
                        generationId={norm.generation_id}
                        stepStatus={stepStatus}
                        feedbackPending={feedbackPending}
                        onFeedback={onFeedback}
                        onClearStep={clearStepFeedback}
                      />
                    );
                  })}
                </div>
              </div>

              {bp.course_suggestions?.length > 0 && (
                <Card>
                  <h3 className="mb-3 font-semibold text-white">Catalog course suggestions</h3>
                  <ul className="space-y-2 text-sm text-slate-400">
                    {bp.course_suggestions.map((c) => (
                      <li key={c} className="flex gap-2">
                        <span className="text-brand-500">▸</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              <Card>
                <h3 className="mb-2 font-semibold text-white">Recommended skill sequence</h3>
                <p className="text-sm text-slate-400">
                  {(bp.recommended_skill_sequence || []).join(" → ")}
                </p>
              </Card>
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <div className="sticky top-6">
            <h3 className="mb-3 font-display text-lg font-semibold text-white">Recent history</h3>
            {histError && <p className="text-sm text-amber-400">{histError}</p>}
            <div className="max-h-[70vh] space-y-3 overflow-y-auto pr-1">
              {history.length === 0 && !histError && (
                <p className="text-sm text-slate-500">No generations yet.</p>
              )}
              {history.map((h) => {
                const go = h.generated_output || {};
                const title = go.base_path?.matched_role || go.matched_role || "Path";
                return (
                  <button
                    key={h.id}
                    type="button"
                    onClick={() => setResult(h.generated_output)}
                    className="w-full rounded-xl border border-slate-700/80 bg-slate-800/40 p-3 text-left text-sm transition hover:border-brand-500/40"
                  >
                    <p className="font-medium text-slate-200">{h.input?.goal}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(h.created_at).toLocaleString()} · {title}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </aside>
      </div>
      <p className="mt-10 text-center text-xs text-slate-600">
        API base: {import.meta.env.VITE_API_URL || "http://localhost:8000"}
      </p>
    </Layout>
  );
}
