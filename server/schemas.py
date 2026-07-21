"""Pydantic request/response models with validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT access token wrapper."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str


class GeneratePathRequest(BaseModel):
    """Input for personalized learning path generation."""

    skills: list[str] = Field(min_length=1, max_length=40)
    goal: str = Field(min_length=2, max_length=200)
    experience_level: Optional[Literal["Beginner", "Intermediate", "Advanced"]] = None
    hours_per_day: float = Field(gt=0, le=24)
    regenerate_smarter: bool = False
    use_cache: bool = True

    @field_validator("skills", mode="before")
    @classmethod
    def strip_skills(cls, v: Any) -> Any:
        """Trim whitespace from each skill string."""
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        return v


class VideoItem(BaseModel):
    """Single YouTube search result."""

    model_config = ConfigDict(extra="ignore")

    title: str = "Video"
    thumbnail: str = ""
    url: str = ""


class SkillGapItem(BaseModel):
    """Skill gap with priority tier and numeric importance."""

    skill: str
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    score: float = Field(ge=0.0, le=1.0)


class GeneratePathResponse(BaseModel):
    """
    Full API payload: ML base path, LLM layer, per-step videos, scored gaps, curated courses.
    """

    model_config = ConfigDict(extra="allow")

    base_path: dict[str, Any]
    ai_roadmap: dict[str, Any]
    videos: dict[str, list[VideoItem]]
    skill_gaps: list[SkillGapItem]
    courses: dict[str, list[str]]
    generation_id: Optional[str] = None


class HistoryItem(BaseModel):
    """One stored generation record."""

    id: str
    user_id: str
    input: dict[str, Any]
    generated_output: dict[str, Any]
    created_at: datetime


class MessageResponse(BaseModel):
    """Generic message payload."""

    message: str


class FeedbackRequest(BaseModel):
    """User feedback on a roadmap step for adaptive learning."""

    step_index: int = Field(ge=0, le=200)
    phase_name: str = Field(default="", max_length=240)
    status: Literal["completed", "not_understood"]
    generation_id: Optional[str] = None


class FeedbackItem(BaseModel):
    """Stored feedback document returned to the client."""

    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    step_index: int
    phase_name: str
    status: str
    generation_id: Optional[str] = None
    created_at: datetime
