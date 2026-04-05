from __future__ import annotations

from dataclasses import dataclass, field

from app.utils.date_parser import PartialDate


@dataclass(slots=True)
class ProvenanceFact:
    nct_id: str
    field_path: str
    field_value: str | int | float | bool | None
    excerpt: str


@dataclass(slots=True)
class InterventionFact:
    nct_id: str
    intervention_name: str
    intervention_type: str | None = None
    cohort_label: str | None = None


@dataclass(slots=True)
class SponsorFact:
    nct_id: str
    sponsor_name: str
    sponsor_class: str | None = None
    cohort_label: str | None = None


@dataclass(slots=True)
class LocationFact:
    nct_id: str
    country: str | None = None
    state: str | None = None
    city: str | None = None
    site_status: str | None = None
    cohort_label: str | None = None


@dataclass(slots=True)
class ConditionFact:
    nct_id: str
    condition: str
    cohort_label: str | None = None


@dataclass(slots=True)
class StudyRecord:
    nct_id: str
    brief_title: str | None = None
    official_title: str | None = None
    overall_status: str | None = None
    start_date: PartialDate | None = None
    completion_date: PartialDate | None = None
    enrollment_count: int | None = None
    phases: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    interventions: list[InterventionFact] = field(default_factory=list)
    sponsors: list[SponsorFact] = field(default_factory=list)
    locations: list[LocationFact] = field(default_factory=list)
    has_results: bool | None = None
    cohort_label: str | None = None


@dataclass(slots=True)
class CanonicalFacts:
    studies: list[StudyRecord] = field(default_factory=list)
    conditions: list[ConditionFact] = field(default_factory=list)
    interventions: list[InterventionFact] = field(default_factory=list)
    sponsors: list[SponsorFact] = field(default_factory=list)
    locations: list[LocationFact] = field(default_factory=list)
    provenance: list[ProvenanceFact] = field(default_factory=list)
