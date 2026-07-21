/**
 * Normalize API payloads: v2 nested shape vs legacy flat ML-only responses (history).
 */
export function normalizePathResult(data) {
  if (!data) return null;
  if (data.base_path) {
    return {
      ...data,
      base_path: data.base_path,
      ai_roadmap: data.ai_roadmap || { detailed_plan: [], explanations: "", tips: [] },
      videos: data.videos || {},
      skill_gaps: data.skill_gaps || [],
      courses: data.courses || {},
      generation_id: data.generation_id || null,
    };
  }
  const gaps = (data.skill_gap_analysis || []).map((s) => ({
    skill: typeof s === "string" ? s : s.skill || "?",
    priority: "MEDIUM",
    score: 0.5,
  }));
  return {
    base_path: { ...data },
    ai_roadmap: {
      detailed_plan: [],
      explanations: data.ai_explanation || "",
      tips: [],
    },
    videos: {},
    skill_gaps: gaps,
    courses: {},
    generation_id: data.generation_id || null,
  };
}

export function getPhases(result) {
  const r = normalizePathResult(result);
  return r?.base_path?.phases || [];
}
