"""
AWS Health Triage - Data Models
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class TriageStatus(str, Enum):
    """Triage status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CarePathway(str, Enum):
    """Care pathway recommendations"""
    EMERGENCY = "emergency"
    URGENT_CARE = "urgent_care"
    PRIMARY_CARE = "primary_care"
    SPECIALIST = "specialist"
    PHYSICAL_THERAPY = "physical_therapy"
    DIGITAL_CARE = "digital_care"
    SELF_CARE = "self_care"


class TriageQuestion(BaseModel):
    """Individual triage question model"""
    id: str
    topic: str
    question: str
    ui_display: str
    response_type: str  # "open_text", "checkbox", "radio", "scale"
    options: Optional[List[str]] = None
    required: bool = True
    depends_on: Optional[str] = None  # Question dependency
    reasoning_required: bool = False
    
    class Config:
        use_enum_values = True


class TriageResponse(BaseModel):
    """Patient response to a triage question"""
    question_id: str
    response: Union[str, List[str], int, float]
    timestamp: datetime
    confidence: Optional[float] = None  # AI confidence in response parsing


class TriageSession(BaseModel):
    """Complete triage session"""
    session_id: str
    patient_id: Optional[str] = None
    status: TriageStatus = TriageStatus.PENDING
    
    # Patient information
    patient_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    gender: Optional[str] = None
    
    # Triage data
    chief_complaint: Optional[str] = None
    symptom_location: Optional[str] = None
    responses: List[TriageResponse] = []
    
    # AI Analysis
    ai_analysis: Optional[Dict[str, Any]] = None
    red_flags: List[str] = []
    risk_factors: List[str] = []
    recommended_pathway: Optional[CarePathway] = None
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    
    # Clinical review
    clinical_review_required: bool = True
    clinical_notes: Optional[str] = None
    final_pathway: Optional[CarePathway] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class TriageDecisionNode(BaseModel):
    """Decision tree node for triage logic"""
    node_id: str
    question: TriageQuestion
    conditions: Dict[str, Any]  # Conditions for this node
    next_nodes: Dict[str, str]  # Response -> next node mapping
    actions: List[str] = []  # Actions to take at this node
    is_terminal: bool = False
    pathway_recommendation: Optional[CarePathway] = None


class TriageDecisionTree(BaseModel):
    """Complete decision tree for triage"""
    tree_id: str
    name: str
    description: str
    version: str
    nodes: Dict[str, TriageDecisionNode]
    entry_point: str  # Starting node ID
    
    class Config:
        use_enum_values = True


class TriageRequest(BaseModel):
    """Request to start or continue triage"""
    session_id: Optional[str] = None
    message: str
    patient_info: Optional[Dict[str, Any]] = None


class TriageStepResponse(BaseModel):
    """Response for a single triage step"""
    session_id: str
    question: Optional[TriageQuestion] = None
    message: str
    is_complete: bool = False
    recommended_pathway: Optional[CarePathway] = None
    confidence_score: Optional[float] = None
    next_steps: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True


class ClinicalReviewRequest(BaseModel):
    """Request for clinical review of triage"""
    session_id: str
    override_pathway: Optional[CarePathway] = None
    clinical_notes: Optional[str] = None
    reviewer_id: str


class TriageAnalytics(BaseModel):
    """Analytics data for triage system"""
    total_sessions: int
    completed_sessions: int
    average_completion_time: Optional[float] = None
    pathway_distribution: Dict[CarePathway, int]
    accuracy_metrics: Optional[Dict[str, float]] = None
    red_flag_frequency: Dict[str, int]
    
    class Config:
        use_enum_values = True


class ConditionCategory(str, Enum):
    """Main medical condition categories"""
    MUSCULOSKELETAL = "musculoskeletal"
    CARDIOVASCULAR = "cardiovascular"  
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    GASTROINTESTINAL = "gastrointestinal"
    GENITOURINARY = "genitourinary"
    DERMATOLOGICAL = "dermatological"
    PSYCHIATRIC = "psychiatric"
    ENDOCRINE = "endocrine"
    INFECTIOUS = "infectious"
    HEMATOLOGICAL = "hematological"
    ONCOLOGICAL = "oncological"
    PEDIATRIC = "pediatric"
    GERIATRIC = "geriatric"
    EMERGENCY = "emergency"


class BodySystem(str, Enum):
    """Body systems for condition classification"""
    SPINE = "spine"
    UPPER_EXTREMITY = "upper_extremity"
    LOWER_EXTREMITY = "lower_extremity"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    HEAD_NECK = "head_neck"
    PELVIS = "pelvis"
    GENERAL = "general"


class ConditionDefinition(BaseModel):
    """Scalable condition definition for thousands of conditions"""
    id: str
    name: str
    category: ConditionCategory
    body_system: Optional[BodySystem] = None
    icd10_codes: List[str] = []
    keywords: List[str] = []
    typical_age_range: Optional[Tuple[int, int]] = None
    common_symptoms: List[str] = []
    red_flags: List[str] = []
    decision_tree_path: Optional[str] = None  # Path to specific decision tree file
    care_pathways: List[CarePathway] = []
    is_active: bool = True
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TriageRule(BaseModel):
    """Flexible triage rules for condition assessment"""
    id: str
    condition_id: str
    question_type: str  # "yes_no", "scale", "multiple_choice", "text"
    question_text: str
    response_options: Optional[List[str]] = None
    scoring_rules: Dict[str, int] = {}  # Response -> Score mapping
    next_question_rules: Dict[str, str] = {}  # Response -> Next Question ID
    red_flag_triggers: List[str] = []
    pathway_rules: Dict[str, CarePathway] = {}  # Score range -> Pathway
    priority: int = 0  # Lower number = higher priority


class TriageFlowState(BaseModel):
    """State management for dynamic triage flows"""
    session_id: str
    current_condition_ids: List[str] = []  # Potential conditions being evaluated
    completed_questions: List[str] = []
    current_question_id: Optional[str] = None
    accumulated_scores: Dict[str, int] = {}  # Condition ID -> Score
    red_flags_detected: List[str] = []
    recommended_pathway: Optional[CarePathway] = None
    confidence_score: float = 0.0
    next_questions: List[str] = []  # Queue of upcoming questions 