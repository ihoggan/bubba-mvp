"""
RDR (Ripple Down Rules) data models.
Defines the shape of rules, questions, fixes, and operator input.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Question types that the operator can answer."""
    YES_NO = "yes_no"
    CHOICE = "choice"
    OPEN = "open"


class Question(BaseModel):
    """A single diagnostic question in a rule's decision tree."""
    id: str = Field(..., description="Unique question ID within rule")
    seq: int = Field(..., description="Sequence number (1-indexed)")
    text: str = Field(..., description="The question to ask the operator")
    type: QuestionType
    choices: Optional[List[str]] = Field(None, description="Valid choices for choice type")
    branches: Dict[str, str] = Field(
        ..., 
        description="Map from answer to next question ID (or fix ID, or escalation)"
    )
    help_text: Optional[str] = Field(None, description="Additional context for the operator")


class Fix(BaseModel):
    """A resolution step or escalation path."""
    title: str = Field(..., description="Short fix title")
    steps: List[str] = Field(..., description="Ordered step-by-step instructions")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence this fix works (0.0-1.0)")
    root_cause: Optional[str] = Field(None, description="Root cause category if known")
    preventive: Optional[str] = Field(None, description="Preventive action or escalation note")


class Rule(BaseModel):
    """A complete RDR rule extracted from ticket patterns."""
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    version: int = Field(1, description="Rule version for tracking updates")
    category: str = Field(..., description="Ticket category (connectivity, access_and_accounts, etc.)")
    subcategory: str = Field(..., description="Ticket subcategory")
    description: str = Field(..., description="Why this rule exists, which tickets it came from")
    
    preconditions: Optional[Dict[str, Any]] = Field(
        None, 
        description="Conditions that must be true for this rule to apply"
    )
    entry_point: str = Field(..., description="ID of the first question to ask")
    questions: List[Question] = Field(..., description="All questions in this rule's tree")
    fixes: Dict[str, Fix] = Field(..., description="All possible resolutions, keyed by ID")
    
    graph_references: Optional[List[str]] = Field(
        None, 
        description="Which parts of the topology graph this rule queries"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for searching/filtering")
    recurrence: int = Field(1, description="Number of times this pattern has appeared")
    last_seen: Optional[str] = Field(None, description="ISO 8601 date last seen")
    status: str = Field("active", description="active or deprecated")
    notes: Optional[str] = Field(None, description="Additional context")


class OperatorInput(BaseModel):
    """What the operator provides when answering a question."""
    rule_id: str
    question_id: str
    answer: str
    timestamp: Optional[str] = None


class LearnedRule(BaseModel):
    """When the operator teaches Bubba something new at a dead end."""
    rule_id: str = Field(default_factory=lambda: f"RDR-USER-{id(object())}_{id(object())}")
    name: str
    category: str
    subcategory: str
    description: str = Field(default="User-learned rule")
    preconditions: Dict[str, Any] = Field(default_factory=dict)
    finding: str = Field(..., description="What the operator found that Bubba didn't predict")
    fix_title: str
    fix_steps: List[str]
    confidence: float = Field(0.70, description="Operator's confidence in this fix")
    created_at: str = Field(..., description="ISO 8601 timestamp")


class ConversationState(BaseModel):
    """State of an ongoing troubleshooting session."""
    session_id: str
    rule_id: str
    current_question_id: str
    operator_answers: Dict[str, str] = Field(
        default_factory=dict, 
        description="Map of question_id -> operator's answer"
    )
    path_taken: List[str] = Field(
        default_factory=list, 
        description="Sequence of question IDs asked"
    )
    status: str = Field("in_progress", description="in_progress, completed, escalated, dead_end")
    final_fix_id: Optional[str] = None
    operator_feedback: Optional[str] = None
    learned_rule: Optional[LearnedRule] = None
