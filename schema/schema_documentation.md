# FRIA Risk Record Schema - Design Documentation

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
