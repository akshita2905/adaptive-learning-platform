import React from "react";

const PRESET_SKILLS = [
  "Python",
  "JavaScript",
  "Java",
  "SQL",
  "React",
  "Node.js",
  "Docker",
  "Kubernetes",
  "AWS",
  "Machine Learning",
  "Statistics",
  "Git",
  "HTML/CSS",
  "TypeScript",
  "Go",
  "Rust",
  "Flutter",
  "Swift",
  "Kotlin",
  "Networking",
];

/**
 * Multi-select toggle chips for skills.
 */
export default function SkillPicker({ value, onChange }) {
  const toggle = (skill) => {
    if (value.includes(skill)) {
      onChange(value.filter((s) => s !== skill));
    } else {
      onChange([...value, skill]);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      {PRESET_SKILLS.map((skill) => {
        const active = value.includes(skill);
        return (
          <button
            key={skill}
            type="button"
            onClick={() => toggle(skill)}
            className={`rounded-full border px-3 py-1.5 text-sm transition ${
              active
                ? "border-brand-500 bg-brand-500/20 text-brand-100"
                : "border-slate-600 bg-slate-800/50 text-slate-300 hover:border-slate-500"
            }`}
          >
            {skill}
          </button>
        );
      })}
    </div>
  );
}
