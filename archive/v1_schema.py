"""
schema.py — Semantic schema for the dissertation annotation pipeline.

Defines enums for Annex III domains, actor roles, system patterns,
rights categories, harm categories, and a RiskRecord dataclass.

v0.3 — Added DPV/VAIR vocabulary alignment maps for JSON-LD export.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any


class AnnexDomain(Enum):
    EMPLOYMENT         = "employment"          # Annex III(4)
    ESSENTIAL_SERVICES = "essential_services"   # Annex III(5a)
    UNKNOWN            = "unknown"

class ActorRole(Enum):
    PROVIDER = "provider"
    DEPLOYER = "deployer"
    OTHER    = "other"

class SystemPattern(Enum):
    LLM_DECISION_SUPPORT   = "llm_decision_support"
    LLM_ASSISTED_SCREENING = "llm_assisted_screening"
    CHATBOT                = "chatbot"
    SUMMARY_ASSISTANT      = "summary_assistant"
    NOT_LLM                = "not_llm"
    UNKNOWN                = "unknown"

class RightCategory(Enum):
    PRIVACY_DATA_PROTECTION  = "privacy_data_protection"
    NON_DISCRIMINATION       = "non_discrimination"
    ACCESS_SOCIAL_PROTECTION = "access_social_protection"
    GOOD_ADMINISTRATION      = "good_administration"
    OTHER                    = "other"

class HarmCategory(Enum):
    UNFAIR_EXCLUSION       = "unfair_exclusion"
    PRIVACY_BREACH         = "privacy_breach"
    MISINFORMATION_ERROR   = "misinformation_error"
    PROCEDURAL_UNFAIRNESS  = "procedural_unfairness"
    OTHER                  = "other"


# ── Vocabulary alignment maps ─────────────────────────────────
# Maps local enum values → published DPV / VAIR / EU-Rights URIs

DOMAIN_URI_MAP = {
    "employment":         "https://w3id.org/vair#Employment",
    "essential_services": "https://w3id.org/vair#EssentialPublicServices",
    "unknown":            "https://w3id.org/vair#UnspecifiedDomain",
}

ACTOR_URI_MAP = {
    "provider": "https://w3id.org/dpv#AIProvider",
    "deployer": "https://w3id.org/dpv#AIDeployer",
    "other":    "https://w3id.org/dpv#Entity",
}

PATTERN_URI_MAP = {
    "llm_decision_support":   "https://w3id.org/vair#DecisionSupport",
    "llm_assisted_screening": "https://w3id.org/vair#AutomatedScreening",
    "chatbot":                "https://w3id.org/vair#Chatbot",
    "summary_assistant":      "https://w3id.org/vair#TextGeneration",
    "not_llm":                "https://w3id.org/vair#NonLLMSystem",
    "unknown":                "https://w3id.org/vair#UnspecifiedPattern",
}

RIGHT_URI_MAP = {
    "privacy_data_protection":  "https://w3id.org/dpv/legal/eu/rights#A8-ProtectionOfPersonalData",
    "non_discrimination":       "https://w3id.org/dpv/legal/eu/rights#A21-NonDiscrimination",
    "access_social_protection": "https://w3id.org/dpv/legal/eu/rights#A34-SocialSecurity",
    "good_administration":      "https://w3id.org/dpv/legal/eu/rights#A41-RightToGoodAdministration",
    "other":                    "https://w3id.org/dpv/legal/eu/rights#FundamentalRights",
}

HARM_URI_MAP = {
    "unfair_exclusion":      "https://w3id.org/dpv/risk#Discrimination",
    "privacy_breach":        "https://w3id.org/dpv/risk#DataBreach",
    "misinformation_error":  "https://w3id.org/dpv/risk#Misinformation",
    "procedural_unfairness": "https://w3id.org/dpv/risk#RightToRemedyImpairment",
    "other":                 "https://w3id.org/dpv/risk#Harm",
}

# ── Standard JSON-LD @context ─────────────────────────────────
JSONLD_CONTEXT = {
    "@vocab":    "https://w3id.org/vair#",
    "vair":      "https://w3id.org/vair#",
    "dpv":       "https://w3id.org/dpv#",
    "dpv-risk":  "https://w3id.org/dpv/risk#",
    "eu-rights": "https://w3id.org/dpv/legal/eu/rights#",
    "dct":       "http://purl.org/dc/terms/",
    "schema":    "https://schema.org/",

    "source":        "dct:source",
    "title":         "dct:title",
    "description":   "dct:description",
    "annexDomain":   {"@id": "vair:hasDomain",        "@type": "@id"},
    "actorRole":     {"@id": "dpv:hasEntity",          "@type": "@id"},
    "systemPattern": {"@id": "vair:hasAICapability",   "@type": "@id"},
    "rights":        {"@id": "eu-rights:affects",       "@type": "@id", "@container": "@set"},
    "harms":         {"@id": "dpv-risk:hasRisk",        "@type": "@id", "@container": "@set"},
}


@dataclass
class RiskRecord:
    source:         str
    source_id:      str
    title:          str
    description:    str
    annex_domain:   AnnexDomain
    actor_role:     ActorRole
    system_pattern: SystemPattern
    rights:         List[RightCategory]
    harms:          List[HarmCategory]
    notes:          str = ""

    def to_row(self) -> Dict[str, Any]:
        return {
            "source":         self.source,
            "source_id":      self.source_id,
            "title":          self.title,
            "description":    self.description,
            "annex_domain":   self.annex_domain.value,
            "actor_role":     self.actor_role.value,
            "system_pattern": self.system_pattern.value,
            "rights":         ";".join(r.value for r in self.rights),
            "harms":          ";".join(h.value for h in self.harms),
            "notes":          self.notes,
        }

    def to_jsonld(self, base_iri: str = "https://example.org/risk-record/") -> Dict[str, Any]:
        """Export as JSON-LD node with vocabulary-aligned URIs."""
        rec_id = (self.source_id or "unknown").replace(" ", "_")
        return {
            "@context":      JSONLD_CONTEXT,
            "@id":           f"{base_iri}{self.source}/{rec_id}",
            "@type":         "vair:RiskRecord",
            "source":        self.source,
            "dct:identifier": self.source_id,
            "title":         self.title,
            "description":   self.description,
            "annexDomain":   DOMAIN_URI_MAP.get(self.annex_domain.value, self.annex_domain.value),
            "actorRole":     ACTOR_URI_MAP.get(self.actor_role.value,  self.actor_role.value),
            "systemPattern": PATTERN_URI_MAP.get(self.system_pattern.value, self.system_pattern.value),
            "rights":        [RIGHT_URI_MAP.get(r.value, r.value) for r in self.rights],
            "harms":         [HARM_URI_MAP.get(h.value,  h.value) for h in self.harms],
            "notes":         self.notes,
        }
