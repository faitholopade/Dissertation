# Defines the ontology v0.1 (domains, roles, rights, harms) and the RiskRecord dataclass used for annotation.

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class AnnexDomain(Enum):
    EMPLOYMENT = "AnnexIII_4_Employment"
    ESSENTIAL_SERVICES = "AnnexIII_5a_EssentialServices"
    UNKNOWN = "Unknown"


class ActorRole(Enum):
    PROVIDER = "Provider"
    DEPLOYER = "Deployer"
    UNKNOWN = "Unknown"


class SystemPattern(Enum):
    LLM_ASSISTED_SCREENING = "LLM_Assisted_Screening"
    LLM_CHATBOT_FRONTEND = "LLM_Chatbot_Frontend"
    LLM_DECISION_SUPPORT = "LLM_Decision_Support"
    LLM_SUMMARISATION_INTERNAL = "LLM_Summarisation_Internal"
    NOT_LLM = "Not_LLM"
    UNKNOWN = "Unknown"


class RightCategory(Enum):
    PRIVACY_DATA_PROTECTION = "Privacy_DataProtection"
    NON_DISCRIMINATION = "Non_Discrimination"
    ACCESS_SOCIAL_PROTECTION = "Access_Social_Protection"
    DECENT_WORKING_CONDITIONS = "Decent_Working_Conditions"


class HarmCategory(Enum):
    UNFAIR_EXCLUSION = "Unfair_Exclusion"
    PRIVACY_BREACH = "Privacy_Breach"
    MISINFORMATION_OR_ERROR = "Misinformation_or_Error"
    PROCEDURAL_UNFAIRNESS = "Procedural_Unfairness"
    OTHER = "Other"


@dataclass
class RiskRecord:
    source: str
    source_id: Optional[str]
    title: str
    description: str

    annex_domain: AnnexDomain = AnnexDomain.UNKNOWN
    actor_role: ActorRole = ActorRole.UNKNOWN
    system_pattern: SystemPattern = SystemPattern.UNKNOWN

    rights: List[RightCategory] = field(default_factory=list)
    harms: List[HarmCategory] = field(default_factory=list)

    notes: Optional[str] = None
