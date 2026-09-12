"""Application-level orchestration for the MVP sandbox."""

from __future__ import annotations

from dataclasses import dataclass

from bubba.diagnosis.domain.models import (
    BeliefLevel,
    Evidence,
    Hypothesis,
    Investigation,
    InvestigationStatus,
    Intervention,
    InterventionStatus,
    Symptom,
    TestDefinition,
    TestExecution,
    TestRisk,
    Verification,
)
from bubba.diagnosis.domain.reasoning import recommend_next_test, update_belief


@dataclass(slots=True)
class InvestigationService:
    """Use-case façade around the domain model."""

    def create_demo(self) -> Investigation:
        """Create a complete synthetic incident illustrating the v2 reasoning model."""
        symptom = Symptom(
            what_is_wrong="Application cannot complete its expected outbound operation.",
            expected_behaviour="Application starts and completes the outbound request successfully.",
            actual_behaviour="Application starts, but the expected operation is blocked before completion.",
            affected_scope="One managed Windows workstation and one signed-in user.",
        )
        investigation = Investigation(title="Application communication failure", symptom=symptom)

        h1 = Hypothesis(
            statement="Network path is unavailable.",
            rationale="The initial user report presents as a communications failure.",
        )
        h2 = Hypothesis(
            statement="DNS/name resolution is failing.",
            rationale="A resolution problem could make an application communication path appear unavailable.",
        )
        h3 = Hypothesis(
            statement="Application-control policy is blocking the process or operation.",
            rationale="The process runs but the expected operation is blocked, making local control a viable explanation.",
        )
        h4 = Hypothesis(
            statement="Application process/configuration is faulty.",
            rationale="A local application defect can cause a communication failure after startup.",
        )
        investigation.hypotheses.extend([h1, h2, h3, h4])

        t1 = TestDefinition(
            name="Direct TCP connectivity test",
            purpose="Determine whether a basic network path to the destination is available.",
            risk=TestRisk.READ_ONLY,
            reversibility="easy",
            observability="high",
            cost="low",
            applicable_hypotheses=[h1.id, h3.id, h4.id],
        )
        t2 = TestDefinition(
            name="DNS resolution test",
            purpose="Determine whether the application destination resolves correctly.",
            risk=TestRisk.READ_ONLY,
            reversibility="easy",
            observability="high",
            cost="low",
            applicable_hypotheses=[h1.id, h2.id],
        )
        t3 = TestDefinition(
            name="Process and policy event inspection",
            purpose="Look for evidence that a local application-control mechanism blocks the operation.",
            risk=TestRisk.READ_ONLY,
            reversibility="easy",
            observability="very high",
            cost="low",
            applicable_hypotheses=[h3.id, h4.id],
        )
        investigation.tests.extend([t1, t2, t3])
        investigation.status = InvestigationStatus.INVESTIGATING

        e1 = Evidence(
            observation="Direct TCP connection to destination:443 succeeds.",
            source="synthetic connectivity test",
            reliability="high",
            context="same workstation and user",
        )
        e2 = Evidence(
            observation="DNS resolution succeeds and matches known-good workstation behaviour.",
            source="synthetic DNS test",
            reliability="high",
            context="same workstation and user",
        )
        e3 = Evidence(
            observation="Process starts, then a Windows application-control event indicates blocking.",
            source="synthetic Windows event evidence",
            reliability="high",
            context="same workstation and user",
        )
        for evidence, hypothesis, strengthens, rationale in [
            (e1, h1, False, "Successful TCP connectivity materially weakens a basic network-path failure explanation."),
            (e2, h2, False, "Successful DNS resolution weakens name-resolution failure as the primary cause."),
            (e3, h3, True, "A policy-enforcement event at the point of failure strongly supports an application-control explanation."),
        ]:
            update_belief(investigation, hypothesis, evidence, strengthens, rationale)

        investigation.executions.extend(
            [
                TestExecution(test_id=t1.id, method="TCP connect", observation=e1.observation, result="success", evidence=[e1]),
                TestExecution(test_id=t2.id, method="Resolve destination", observation=e2.observation, result="success", evidence=[e2]),
                TestExecution(test_id=t3.id, method="Inspect process and Windows event log", observation=e3.observation, result="blocked", evidence=[e3]),
            ]
        )
        investigation.add_event("diagnostic_test", "Connectivity test succeeded.", {"test": t1.name})
        investigation.add_event("diagnostic_test", "DNS resolution succeeded.", {"test": t2.name})
        investigation.add_event("diagnostic_test", "Policy enforcement evidence observed.", {"test": t3.name})

        remediation = Intervention(
            description="Deploy the intended application-control policy exception.",
            expected_effect="Policy should allow the application operation.",
            target="Synthetic managed Windows endpoint",
            status=InterventionStatus.EXECUTED,
        )
        investigation.interventions.append(remediation)
        investigation.add_event(
            "intervention_executed",
            "Policy remediation attempted but expected state is not present.",
            {"status": "appears_ineffective"},
        )

        # Crucially, diagnosis remains strong while remediation is investigated separately.
        remediation_evidence = Evidence(
            observation="Expected policy exception is absent from the endpoint because the endpoint is in the wrong management scope.",
            source="synthetic management-context inspection",
            reliability="high",
            context="device/user policy assignment context",
        )
        update_belief(
            investigation,
            h3,
            remediation_evidence,
            True,
            "The failed remediation is explained by policy-management context; it does not contradict the original blocking-policy diagnosis.",
        )
        remediation.status = InterventionStatus.FAILED_TO_APPLY
        investigation.add_event(
            "remediation_failure_classified",
            "Diagnosis retained; remediation classified as failed to apply.",
            {"diagnosis": h3.statement, "failure_mode": "management_context"},
        )

        verification_evidence = Evidence(
            observation="Correct policy scope is now applied, the application-control event is absent, and the application operation succeeds.",
            source="synthetic post-remediation verification",
            reliability="high",
            context="same endpoint and user",
        )
        verification = Verification(
            criterion="Application completes the expected outbound operation.",
            method="Repeat original user workflow and inspect enforcement evidence.",
            expected_result="Operation succeeds without policy block.",
            actual_result=verification_evidence.observation,
            passed=True,
            evidence_ids=[verification_evidence.id],
        )
        investigation.verifications.append(verification)
        remediation.status = InterventionStatus.VERIFIED_EFFECTIVE
        h3.belief = BeliefLevel.CONFIRMED
        investigation.root_cause = "Application-control policy blocked the operation because the intended policy remediation was initially outside the endpoint's effective management scope."
        investigation.status = InvestigationStatus.RESOLVED
        investigation.engineer_confirmed = True
        investigation.add_event(
            "verification_passed",
            "Independent verification confirms service behaviour is restored and supports the causal chain.",
            {"verification_id": str(verification.id)},
        )
        investigation.add_event(
            "root_cause_confirmed",
            "Engineer confirmed the root cause.",
            {"root_cause": investigation.root_cause},
        )
        return investigation

    def next_test(self, investigation: Investigation):
        """Return an explainable next-test recommendation."""
        return recommend_next_test(investigation)
