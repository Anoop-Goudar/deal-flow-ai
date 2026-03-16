from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


Actor = Literal[
    "client",
    "relationship_manager",
    "loan_specialist",
    "credit_card_specialist",
    "trade_finance_specialist",
    "admin",
]

EligibilityStatus = Literal["Eligible", "Not eligible", "Eligibility incomplete"]
TaskStatus = Literal["pending", "in_progress", "completed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Client(BaseModel):
    client_id: str
    name: str
    type: Literal["business", "individual"]
    business_turnover: float | None = None
    business_years: int | None = None
    annual_revenue: float | None = None
    monthly_salary: float | None = None
    collateral_available: bool | None = None
    import_export_activity: bool | None = None
    notes: list[str] = Field(default_factory=list)


class ConversationEvent(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    actor: Actor
    message: str


class Task(BaseModel):
    task_id: str
    client_id: str
    product: str
    assigned_to: Actor
    action: str
    status: TaskStatus = "pending"


class ProductRecommendation(BaseModel):
    product: str
    eligibility: EligibilityStatus
    assigned_agent: Actor
    rationale: str
    next_action: str
    confidence: float = 0.0
    policy_excerpt: str
    retrieved_chunk: str | None = None
    retrieval_score: float | None = None
    missing_fields: list[str] = Field(default_factory=list)


class PolicyDocument(BaseModel):
    policy_id: str
    product: str
    title: str
    category: str
    policy_text: str
    min_business_years: int | None = None
    min_turnover: float | None = None
    required_collateral: bool | None = None
    requires_import_export_activity: bool | None = None
    assigned_agent: Actor
    next_action: str


class RetrievalMatch(BaseModel):
    chunk_id: str
    policy_id: str
    product: str
    title: str
    text: str
    score: float


class NeedAnalysisResult(BaseModel):
    summary: str
    financial_needs: list[str]
    confidence: Literal["low", "medium", "high"]
    raw_signals: list[str] = Field(default_factory=list)


class ExtractedAttributes(BaseModel):
    business_turnover: float | None = None
    business_years: int | None = None
    annual_revenue: float | None = None
    monthly_salary: float | None = None
    collateral_available: bool | None = None
    import_export_activity: bool | None = None
    notes: list[str] = Field(default_factory=list)


class AddMessageRequest(BaseModel):
    client_id: str
    actor: Actor
    message: str


class AddMessageResponse(BaseModel):
    status: Literal["message_added"]
    event: ConversationEvent
    workspace: "WorkspaceData"


class RunPipelineRequest(BaseModel):
    client_id: str


class UpdateTaskStatusRequest(BaseModel):
    status: TaskStatus


class PipelineResult(BaseModel):
    client_id: str
    summary: str
    confidence: Literal["low", "medium", "high"]
    detected_needs: list[str]
    extracted_attributes: ExtractedAttributes
    recommendations: list[ProductRecommendation]
    tasks: list[Task]


class WorkspaceData(BaseModel):
    client: Client
    conversation: list[ConversationEvent]
    pipeline_result: PipelineResult | None = None
    tasks: list[Task]
    suggested_replies: list["SuggestedReply"] = Field(default_factory=list)


class SuggestedReply(BaseModel):
    title: str
    message: str


class AppStateSnapshot(BaseModel):
    clients: list[Client]
    conversations: dict[str, list[ConversationEvent]]
    recommendations: dict[str, PipelineResult]
    tasks: list[Task]
