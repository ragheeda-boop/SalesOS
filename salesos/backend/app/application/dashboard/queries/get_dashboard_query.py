from pydantic import BaseModel, Field


class DashboardQuery(BaseModel):
    period: str = Field(default="today", description="'today' | 'week' | 'month' | 'quarter'")
    fields: list[str] | None = Field(default=None, description="Widget IDs to include, e.g. ['mission-center', 'ai-brief']. None = all widgets.")
