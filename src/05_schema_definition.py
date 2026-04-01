"""Step 05: Define and export the FRIA risk semantic schema.

Generates the ontology schema in JSON-LD and Turtle formats, aligned with
DPV, DPV-Risk, VAIR, and EU-Rights vocabularies. Also produces schema
documentation and an example risk record.

Outputs:
    schema/fria_risk_schema.jsonld
    schema/fria_risk_schema.ttl
    schema/example_risk_record.jsonld
    schema/schema_documentation.md
"""

import json, os

JSONLD_CONTEXT = {
    "@context": {
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

        "RiskRecord": "fria:RiskRecord",
        "source": {"@id": "dct:source", "@type": "xsd:string"},
        "sourceId": {"@id": "dct:identifier", "@type": "xsd:string"},
        "title": {"@id": "dct:title", "@type": "xsd:string"},
        "description": {"@id": "dct:description", "@type": "xsd:string"},
        "dateRecorded": {"@id": "dct:date", "@type": "xsd:date"},

        "annexDomain": {
            "@id": "fria:annexDomain",
            "@type": "@vocab",
            "@context": {
                "employment": "aiact:HighRiskAI-Employment",
                "essential_services": "aiact:HighRiskAI-EssentialServices",
                "unknown": "fria:UnclassifiedDomain"
            }
        },

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

        "actorRole": {
            "@id": "fria:actorRole",
            "@type": "@vocab",
            "@context": {
                "provider": "aiact:AIProvider",
                "deployer": "aiact:AIDeployer",
                "affected_person": "aiact:AffectedPerson"
            }
        },

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


TURTLE_SCHEMA = """@prefix fria: <https://example.org/fria-risk-schema#> .
@prefix dpv: <https://w3id.org/dpv#> .
@prefix dpv-risk: <https://w3id.org/dpv/risk#> .
@prefix dpv-rights: <https://w3id.org/dpv/legal/eu/rights#> .
@prefix aiact: <https://w3id.org/dpv/legal/eu/aiact#> .
@prefix vair: <https://w3id.org/vair#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<https://example.org/fria-risk-schema>
    a owl:Ontology ;
    dct:title "FRIA Risk Record Schema"@en ;
    dct:description "An ontology for representing AI risk records aligned with EU AI Act Annex III, designed to support Fundamental Rights Impact Assessments (FRIA). Developed as part of MSc dissertation research at Trinity College Dublin."@en ;
    dct:creator "Faith Olopade" ;
    dct:created "2026"^^xsd:gYear ;
    owl:imports <https://w3id.org/dpv> ;
    rdfs:seeAlso <https://w3id.org/dpv/legal/eu/aiact> ,
                 <https://w3id.org/vair> .

fria:RiskRecord
    a owl:Class ;
    rdfs:label "Risk Record"@en ;
    rdfs:comment "A single documented AI incident or use case annotated for fundamental rights risk assessment."@en ;
    rdfs:subClassOf dpv-risk:RiskAssessment .

fria:annexDomain
    a owl:ObjectProperty ;
    rdfs:label "Annex III Domain"@en ;
    rdfs:comment "The EU AI Act Annex III high-risk application domain."@en ;
    rdfs:domain fria:RiskRecord ;
    rdfs:range fria:AnnexDomain .

fria:systemPattern
    a owl:ObjectProperty ;
    rdfs:label "System Pattern"@en ;
    rdfs:comment "The AI system architecture or deployment pattern."@en ;
    rdfs:domain fria:RiskRecord ;
    rdfs:range fria:SystemPattern .

fria:rightsImpacted
    a owl:ObjectProperty ;
    rdfs:label "Rights Impacted"@en ;
    rdfs:comment "Fundamental rights affected by the AI system."@en ;
    rdfs:domain fria:RiskRecord ;
    rdfs:range dpv:Right .

fria:harmsIdentified
    a owl:ObjectProperty ;
    rdfs:label "Harms Identified"@en ;
    rdfs:comment "Specific harms documented in the risk record."@en ;
    rdfs:domain fria:RiskRecord ;
    rdfs:range dpv-risk:Harm .

fria:annotationMethod
    a owl:ObjectProperty ;
    rdfs:label "Annotation Method"@en ;
    rdfs:comment "The method used to produce this annotation."@en ;
    rdfs:domain fria:RiskRecord ;
    rdfs:range fria:AnnotationMethod .

fria:confidence
    a owl:DatatypeProperty ;
    rdfs:label "Confidence Score"@en ;
    rdfs:domain fria:RiskRecord ;
    rdfs:range xsd:float .

fria:AnnexDomain a owl:Class ;
    rdfs:label "Annex III Domain"@en .

fria:Employment
    a fria:AnnexDomain ;
    rdfs:label "Employment, workers management"@en ;
    skos:notation "Annex III(4)" ;
    rdfs:comment "AI systems for recruitment, selection, workplace monitoring, task allocation, performance evaluation (Art. 6(2), Annex III(4))."@en ;
    owl:sameAs aiact:HighRiskAI-Employment .

fria:EssentialServices
    a fria:AnnexDomain ;
    rdfs:label "Essential public services and benefits"@en ;
    skos:notation "Annex III(5a)" ;
    rdfs:comment "AI systems evaluating eligibility for public assistance, healthcare, benefits; credit scoring; emergency dispatch (Art. 6(2), Annex III(5a))."@en ;
    owl:sameAs aiact:HighRiskAI-EssentialServices .

fria:SystemPattern a owl:Class ;
    rdfs:label "AI System Pattern"@en ;
    rdfs:comment "Taxonomy of AI system architectures relevant to risk assessment."@en .

fria:LLMDecisionSupport a fria:SystemPattern ;
    rdfs:label "LLM Decision Support"@en ;
    rdfs:comment "System uses a large language model to assist or automate decisions."@en .

fria:LLMAssistedScreening a fria:SystemPattern ;
    rdfs:label "LLM-Assisted Screening"@en ;
    rdfs:comment "System uses LLM for screening, filtering, or ranking."@en .

fria:Chatbot a fria:SystemPattern ;
    rdfs:label "Chatbot / Virtual Assistant"@en ;
    rdfs:comment "Conversational AI system interacting with users."@en .

fria:SummaryAssistant a fria:SystemPattern ;
    rdfs:label "Summary Assistant"@en ;
    rdfs:comment "System that generates summaries or reports."@en .

fria:SurveillanceMonitor a fria:SystemPattern ;
    rdfs:label "Surveillance / Monitor"@en ;
    rdfs:comment "System that monitors or surveils individuals."@en .

fria:ProfilingScoring a fria:SystemPattern ;
    rdfs:label "Profiling / Scoring"@en ;
    rdfs:comment "System that creates profiles or risk scores."@en .

fria:ClassificationTriage a fria:SystemPattern ;
    rdfs:label "Classification / Triage"@en ;
    rdfs:comment "System that classifies or triages cases."@en .

fria:ResourceAllocation a fria:SystemPattern ;
    rdfs:label "Resource Allocation"@en ;
    rdfs:comment "System that allocates resources or benefits."@en .

fria:TraditionalML a fria:SystemPattern ;
    rdfs:label "Traditional ML (non-LLM)"@en ;
    rdfs:comment "System using conventional machine learning without LLM components."@en .

fria:AnnotationMethod a owl:Class ;
    rdfs:label "Annotation Method"@en .

fria:KeywordAnnotation a fria:AnnotationMethod ;
    rdfs:label "Keyword-based Annotation"@en ;
    rdfs:comment "Classification via keyword/regex matching against predefined dictionaries."@en .

fria:LLMAnnotation a fria:AnnotationMethod ;
    rdfs:label "LLM-based Annotation"@en ;
    rdfs:comment "Classification via prompted large language model (GPT-4o)."@en .

fria:HybridAnnotation a fria:AnnotationMethod ;
    rdfs:label "Hybrid Annotation"@en ;
    rdfs:comment "Union of keyword and LLM annotations, prioritising non-unknown labels."@en .

fria:ManualAnnotation a fria:AnnotationMethod ;
    rdfs:label "Manual Annotation"@en ;
    rdfs:comment "Human expert annotation via Label Studio."@en .
"""


SCHEMA_DOCS = """# FRIA Risk Record Schema - Design Documentation

## Purpose
This schema defines a lightweight ontology for representing AI risk records
aligned with the EU AI Act Annex III framework. It supports the structured
annotation and retrieval of AI incident data for Fundamental Rights Impact
Assessments (FRIA).

## Design Principles
1. **Alignment with existing vocabularies**: Reuses DPV, VAIR, and AIRO concepts
   wherever possible, extending only where gaps exist.
2. **Annex III grounding**: Domain classification maps directly to Art. 6(2) and
   Annex III of the EU AI Act.
3. **Multi-method annotation**: Tracks provenance of each annotation (keyword,
   LLM, hybrid, manual) to support reproducibility and method comparison.
4. **Minimality**: Only concepts needed for the dissertation's research questions
   are included; the schema is designed to be extensible.

## Class Hierarchy

```
dpv-risk:RiskAssessment
  +-- fria:RiskRecord
        +-- fria:annexDomain -> fria:AnnexDomain
        |     +-- fria:Employment (Annex III(4))
        |     +-- fria:EssentialServices (Annex III(5a))
        +-- fria:systemPattern -> fria:SystemPattern
        |     +-- fria:LLMDecisionSupport
        |     +-- fria:LLMAssistedScreening
        |     +-- fria:Chatbot
        |     +-- fria:SummaryAssistant
        |     +-- fria:SurveillanceMonitor
        |     +-- fria:ProfilingScoring
        |     +-- fria:ClassificationTriage
        |     +-- fria:ResourceAllocation
        |     +-- fria:TraditionalML
        +-- fria:rightsImpacted -> dpv:Right
        |     +-- dpv-rights:A21-NonDiscrimination
        |     +-- dpv-rights:A8-ProtectionOfPersonalData
        |     +-- dpv-rights:A34-SocialSecurityAndAssistance
        |     +-- dpv-rights:A41-RightToGoodAdministration
        +-- fria:harmsIdentified -> dpv-risk:Harm
        |     +-- dpv-risk:Discrimination (unfair_exclusion)
        |     +-- dpv-risk:DataBreach (privacy_breach)
        |     +-- dpv-risk:MisinformationDissemination
        |     +-- dpv-risk:ViolationOfRights (procedural_unfairness)
        +-- fria:annotationMethod -> fria:AnnotationMethod
              +-- fria:KeywordAnnotation
              +-- fria:LLMAnnotation
              +-- fria:HybridAnnotation
              +-- fria:ManualAnnotation
```

## Vocabulary Alignment

| Schema Concept | DPV Equivalent | VAIR Equivalent | EU AI Act Reference |
|---|---|---|---|
| `fria:Employment` | - | `vair:Employment` | Annex III(4) |
| `fria:EssentialServices` | - | `vair:EssentialServices` | Annex III(5a) |
| `fria:rightsImpacted` | `dpv:hasRight` | - | Art. 27 FRIA |
| `fria:harmsIdentified` | `dpv-risk:hasRisk` | `vair:hasHarm` | Recital 48 |
| `fria:ProfilingScoring` | `dpv-tech:Profiling` | - | Art. 6(2) |
| `fria:SurveillanceMonitor` | `dpv-tech:Surveillance` | - | Annex III(1) |

## Data Sources Modelled

| Source | Records | Coverage |
|---|---|---|
| AIAAIC Repository | ~100 | AI incidents from news, NGO reports |
| US Federal AI Inventory | ~30 | Government AI use cases |
| ECtHR Case Law | ~20 | Fundamental rights legal precedents |

## Reproducibility
All annotation scripts, keyword dictionaries, LLM prompts, and evaluation
code are version-controlled. The JSON-LD export (`risk_records.jsonld`) can
be validated against this schema using standard JSON-LD processors.
"""


EXAMPLE_RECORD = {
    "@context": JSONLD_CONTEXT["@context"],
    "@type": "RiskRecord",
    "@id": "fria:record/AIAAIC0554",
    "source": "AIAAIC",
    "sourceId": "AIAAIC0554",
    "title": "Netherlands childcare benefits fraud assessments automation",
    "description": "The Dutch tax authority used an automated system to flag families for childcare benefit fraud, disproportionately targeting ethnic minorities.",
    "annexDomain": "essential_services",
    "systemPattern": "profiling_scoring",
    "rightsImpacted": ["non_discrimination", "privacy_data_protection", "access_social_protection"],
    "harmsIdentified": ["unfair_exclusion", "privacy_breach"],
    "actorRole": "deployer",
    "annotationMethod": "hybrid",
    "confidence": 0.92,
    "annotatorNote": "Well-documented case; Dutch court ruling confirmed rights violations."
}


def main():
    with open("schema/fria_risk_schema.jsonld", "w", encoding="utf-8") as f:
        json.dump(JSONLD_CONTEXT, f, indent=2)
    print("schema/fria_risk_schema.jsonld")

    with open("schema/fria_risk_schema.ttl", "w", encoding="utf-8") as f:
        f.write(TURTLE_SCHEMA)
    print("schema/fria_risk_schema.ttl")

    with open("schema/schema_documentation.md", "w", encoding="utf-8") as f:
        f.write(SCHEMA_DOCS)
    print("schema/schema_documentation.md")

    with open("schema/example_risk_record.jsonld", "w", encoding="utf-8") as f:
        json.dump(EXAMPLE_RECORD, f, indent=2)
    print("schema/example_risk_record.jsonld")

    print("\n  To re-export all records with the new schema, run:")
    print("    python export_semantic_v2.py")


if __name__ == "__main__":
    main()
