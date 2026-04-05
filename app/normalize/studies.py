from __future__ import annotations

from app.models.fetch_plan import FetchExecutionResult
from app.normalize.facts import CanonicalFacts, ConditionFact, InterventionFact, LocationFact, ProvenanceFact, SponsorFact, StudyRecord
from app.normalize.provenance import build_excerpt
from app.utils.date_parser import parse_partial_date
from app.utils.field_extractor import deep_get, ensure_list


def normalize_fetch_result(result: FetchExecutionResult) -> CanonicalFacts:
    facts = CanonicalFacts()
    for batch in result.batches:
        for study in batch.studies:
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
            conditions_module = protocol.get("conditionsModule", {})
            design_module = protocol.get("designModule", {})
            interventions_module = protocol.get("armsInterventionsModule", {})
            locations_module = protocol.get("contactsLocationsModule", {})

            nct_id = identification.get("nctId")
            if not nct_id:
                continue

            study_record = StudyRecord(
                nct_id=nct_id,
                brief_title=identification.get("briefTitle"),
                official_title=identification.get("officialTitle"),
                overall_status=status.get("overallStatus"),
                start_date=parse_partial_date(deep_get(status, "startDateStruct", "date")),
                completion_date=parse_partial_date(deep_get(status, "completionDateStruct", "date")),
                enrollment_count=deep_get(design_module, "enrollmentInfo", "count"),
                phases=list(ensure_list(design_module.get("phases"))),
                conditions=list(ensure_list(conditions_module.get("conditions"))),
                cohort_label=batch.label,
            )

            if study_record.brief_title:
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.identificationModule.briefTitle",
                        field_value=study_record.brief_title,
                        excerpt=build_excerpt("briefTitle", study_record.brief_title),
                    )
                )
            if study_record.overall_status:
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.statusModule.overallStatus",
                        field_value=study_record.overall_status,
                        excerpt=build_excerpt("overallStatus", study_record.overall_status),
                    )
                )
            if study_record.start_date:
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.statusModule.startDateStruct.date",
                        field_value=study_record.start_date.raw,
                        excerpt=build_excerpt("startDateStruct.date", study_record.start_date.raw),
                    )
                )
            if study_record.completion_date:
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.statusModule.completionDateStruct.date",
                        field_value=study_record.completion_date.raw,
                        excerpt=build_excerpt("completionDateStruct.date", study_record.completion_date.raw),
                    )
                )
            if study_record.enrollment_count is not None:
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.designModule.enrollmentInfo.count",
                        field_value=study_record.enrollment_count,
                        excerpt=build_excerpt("enrollmentInfo.count", study_record.enrollment_count),
                    )
                )

            for condition in study_record.conditions:
                condition_fact = ConditionFact(nct_id=nct_id, condition=condition, cohort_label=batch.label)
                facts.conditions.append(condition_fact)
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.conditionsModule.conditions",
                        field_value=condition,
                        excerpt=build_excerpt("conditions", condition),
                    )
                )

            lead_sponsor = deep_get(sponsor_module, "leadSponsor", "name")
            lead_sponsor_class = deep_get(sponsor_module, "leadSponsor", "class")
            if lead_sponsor:
                sponsor_fact = SponsorFact(
                    nct_id=nct_id,
                    sponsor_name=lead_sponsor,
                    sponsor_class=lead_sponsor_class,
                    cohort_label=batch.label,
                )
                study_record.sponsors.append(sponsor_fact)
                facts.sponsors.append(sponsor_fact)
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
                        field_value=lead_sponsor,
                        excerpt=build_excerpt("leadSponsor.name", lead_sponsor),
                    )
                )
                if lead_sponsor_class:
                    facts.provenance.append(
                        ProvenanceFact(
                            nct_id=nct_id,
                            field_path="protocolSection.sponsorCollaboratorsModule.leadSponsor.class",
                            field_value=lead_sponsor_class,
                            excerpt=build_excerpt("leadSponsor.class", lead_sponsor_class),
                        )
                    )
            for collaborator in ensure_list(sponsor_module.get("collaborators")):
                name = collaborator.get("name") if isinstance(collaborator, dict) else collaborator
                if not name:
                    continue
                sponsor_fact = SponsorFact(nct_id=nct_id, sponsor_name=name, cohort_label=batch.label)
                study_record.sponsors.append(sponsor_fact)
                facts.sponsors.append(sponsor_fact)
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.sponsorCollaboratorsModule.collaborators.name",
                        field_value=name,
                        excerpt=build_excerpt("collaborators.name", name),
                    )
                )

            for intervention in ensure_list(interventions_module.get("interventions")):
                if not isinstance(intervention, dict):
                    continue
                name = intervention.get("name")
                if not name:
                    continue
                intervention_fact = InterventionFact(
                    nct_id=nct_id,
                    intervention_name=name,
                    intervention_type=intervention.get("type"),
                    cohort_label=batch.label,
                )
                study_record.interventions.append(intervention_fact)
                facts.interventions.append(intervention_fact)
                facts.provenance.append(
                    ProvenanceFact(
                        nct_id=nct_id,
                        field_path="protocolSection.armsInterventionsModule.interventions.name",
                        field_value=name,
                        excerpt=build_excerpt("interventions.name", name),
                    )
                )

            for location in ensure_list(locations_module.get("locations")):
                if not isinstance(location, dict):
                    continue
                location_fact = LocationFact(
                    nct_id=nct_id,
                    country=location.get("country"),
                    state=location.get("state"),
                    city=location.get("city"),
                    site_status=location.get("status"),
                    cohort_label=batch.label,
                )
                study_record.locations.append(location_fact)
                facts.locations.append(location_fact)
                if location_fact.country:
                    facts.provenance.append(
                        ProvenanceFact(
                            nct_id=nct_id,
                            field_path="protocolSection.contactsLocationsModule.locations.country",
                            field_value=location_fact.country,
                            excerpt=build_excerpt("locations.country", location_fact.country),
                        )
                    )

            facts.studies.append(study_record)
    return facts
