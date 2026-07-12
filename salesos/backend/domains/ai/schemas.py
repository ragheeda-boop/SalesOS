"""Pydantic schemas for the AI domain."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    version: str = Field(default="1.0")
    template: str = Field(..., min_length=1)
    variables: list[str] = Field(default_factory=list)
    output_schema: dict[str, Any] | None = None
    domain: str = ""


class EvaluateRequest(BaseModel):
    prompt_id: str
    input: str
    output: str
    expected: str | None = None
    metrics: list[str] | None = None


class GenerateRequest(BaseModel):
    prompt_template_id: str
    variables: dict[str, Any] = Field(default_factory=dict)
    provider: str = "openai"
    model: str | None = None


class ActivateRequest(BaseModel):
    id: str
    version: str
