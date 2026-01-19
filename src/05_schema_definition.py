#!/usr/bin/env python3
"""
schema_definition.py  –  Generate formal schema artefacts for the dissertation.

Outputs:
  1. fria_risk_schema.jsonld     – JSON-LD context defining the ontology
  2. fria_risk_schema.ttl        – Turtle/OWL serialisation
  3. schema_documentation.md     – Human-readable schema docs for Chapter 4

The schema aligns with:
  - DPV (Data Privacy Vocabulary) v2 – https://w3id.org/dpv
  - VAIR (Vocabulary for AI Risk) – https://w3id.org/vair
  - AIRO (AI Risk Ontology) – https://w3id.org/airo
  - EU AI Act Annex III categories

Run:
    python schema_definition.py
"""

import json, os

# ─── JSON-LD Context ─────────────────────────────────────────────────

JSONLD_CONTEXT = {
    "@context": {
        # Namespace prefixes
        "fria": "https://example.org/fria-risk-schema#",
        "dpv": "https://w3id.org/dpv#",
        "dpv-risk": "https://w3id.org/dpv/risk#",
        "dpv-rights": "https://w3id.org/dpv/legal/eu/rights#",
        "dpv-tech": "https://w3id.org/dpv/tech#",
        "vair": "https://w3id.org/vair#",
        "airo": "https://w3id.org/airo#",
        "aiact": "https://w3id.org/dpv/legal/eu/aiact#",
        "dct": "http://purl.org/dc/terms/",
        "schema": "http://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "skos": "http://www.w3.org/2004/02/skos/core#",

        # Core record properties
        "RiskRecord": "fria:RiskRecord",
        "source": {"@id": "dct:source", "@type": "xsd:string"},
        "sourceId": {"@id": "dct:identifier", "@type": "xsd:string"},
        "title": {"@id": "dct:title", "@type": "xsd:string"},
        "description": {"@id": "dct:description", "@type": "xsd:string"},
        "dateRecorded": {"@id": "dct:date", "@type": "xsd:date"},

        # AI Act alignment
        "annexDomain": {
            "@id": "fria:annexDomain",
            "@type": "@vocab",
            "@context": {
                "employment": "aiact:HighRiskAI-Employment",
                "essential_services": "aiact:HighRiskAI-EssentialServices",
                "unknown": "fria:UnclassifiedDomain"
            }
        },

        # System characterisation
        "systemPattern": {
            "@id": "fria:systemPattern",
            "@type": "@vocab",
            "@context": {
                "llm_decision_support": "fria:LLMDecisionSupport",
                "llm_assisted_screening": "fria:LLMAssistedScreening",
                "chatbot": "fria:Chatbot",
                "summary_assistant": "fria:SummaryAssistant",
                "surveillance_monitor": "fria:SurveillanceMonitor",
                "profiling_scoring": "fria:ProfilingScoring",
                "classification_triage": "fria:ClassificationTriage",
                "resource_allocation": "fria:ResourceAllocation",
                "not_llm": "fria:TraditionalML",
                "unknown": "fria:UnclassifiedPattern"
            }
        },

        # Fundamental rights (aligned with EU Charter + DPV)
        "rightsImpacted": {
            "@id": "fria:rightsImpacted",
            "@container": "@set",
            "@context": {
                "non_discrimination": "dpv-rights:A21-NonDiscrimination",
                "privacy_data_protection": "dpv-rights:A8-ProtectionOfPersonalData",
                "access_social_protection": "dpv-rights:A34-SocialSecurityAndAssistance",
                "good_administration": "dpv-rights:A41-RightToGoodAdministration",
                "other": "fria:OtherRight"
            }
        },

        # Harms (aligned with DPV Risk extension)
        "harmsIdentified": {
            "@id": "fria:harmsIdentified",
            "@container": "@set",
            "@context": {
                "unfair_exclusion": "dpv-risk:Discrimination",
                "privacy_breach": "dpv-risk:DataBreach",
                "misinformation_error": "dpv-risk:MisinformationDissemination",
                "procedural_unfairness": "dpv-risk:ViolationOfRights",
                "other": "dpv-risk:Harm"
            }
        },

        # Actor roles
        "actorRole": {
            "@id": "fria:actorRole",
            "@type": "@vocab",
            "@context": {
                "provider": "aiact:AIProvider",
                "deployer": "aiact:AIDeployer",
                "affected_person": "aiact:AffectedPerson"
            }
        },

        # Annotation metadata
        "annotationMethod": {
            "@id": "fria:annotationMethod",
            "@type": "@vocab",
            "@context": {
                "keyword": "fria:KeywordAnnotation",
                "llm": "fria:LLMAnnotation",
                "hybrid": "fria:HybridAnnotation",
                "manual": "fria:ManualAnnotation"
            }
        },
        "confidence": {"@id": "fria:confidence", "@type": "xsd:float"},
        "annotatorNote": {"@id": "fria:annotatorNote", "@type": "xsd:string"},
    }
}


# ─── Turtle / OWL Schema ────────────────────────────────────────────

TURTLE_SCHEMA = """@prefix fria: <https://example.org/fria-risk-schema#> .
@prefix dpv: <https://w3id.org/dpv#> .
@prefix dpv-risk: <https://w3id.org/dpv/risk#> .
@prefix dpv-rights: <https://w3id.org/dpv/legal/eu/rights#> .
@prefix aiact: <https://w3id.org/dpv/legal/eu/aiact#> .
@prefix vair: <https://w3id.org/vair#> .
