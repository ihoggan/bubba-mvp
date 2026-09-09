"""
Tests for the RDR engine, models, and branching logic.
"""

import pytest
from pathlib import Path
from src.engine import RDREngine
from src.models import Rule, Question, Fix, ConversationState, QuestionType


@pytest.fixture
def engine():
    """Load the engine with test rules."""
    rules_file = Path(__file__).parent.parent / "data" / "rdr_rules.json"
    return RDREngine(rules_file)


class TestEngineLoading:
    """Test rule loading and retrieval."""

    def test_engine_loads_rules(self, engine):
        """Engine should load all rules from JSON."""
        assert len(engine.rules) > 0
        assert "RDR-CONN-001" in engine.rules

    def test_get_rule(self, engine):
        """Engine should retrieve a specific rule."""
        rule = engine.get_rule("RDR-CONN-001")
        assert rule is not None
        assert rule.name == "Single endpoint no link - daisy chain issue"

    def test_get_nonexistent_rule(self, engine):
        """Engine should return None for unknown rule."""
        rule = engine.get_rule("RDR-FAKE-999")
        assert rule is None

    def test_rule_validation(self, engine):
        """All loaded rules should be valid Pydantic models."""
        for rule_id, rule in engine.rules.items():
            assert rule.rule_id == rule_id
            assert rule.entry_point
            assert len(rule.questions) > 0
            assert len(rule.fixes) > 0


class TestQuestionSequencing:
    """Test question navigation and branching."""

    def test_get_first_question(self, engine):
        """Engine should return the entry-point question."""
        q = engine.get_first_question("RDR-CONN-001")
        assert q is not None
        assert q.id == "q1_phone_works"
        assert q.seq == 1

    def test_get_specific_question(self, engine):
        """Engine should retrieve a question by rule and question ID."""
        q = engine.get_question("RDR-CONN-001", "q2_check_switch")
        assert q is not None
        assert q.seq == 2
        assert "MAC address" in q.text

    def test_question_has_valid_branches(self, engine):
        """All questions should have valid branch destinations."""
        for rule_id, rule in engine.rules.items():
            for question in rule.questions:
                for destination in question.branches.values():
                    # Destination should be a question, fix, or escalate
                    is_question = any(q.id == destination for q in rule.questions)
                    is_fix = destination in rule.fixes
                    is_escalate = destination == "escalate" or destination.startswith("escalate_")
                    
                    assert is_question or is_fix or is_escalate, \
                        f"Invalid branch destination '{destination}' in {rule_id}/{question.id}"


class TestAnswerProcessing:
    """Test how the engine processes operator answers."""

    def test_yes_no_answer_yes(self, engine):
        """Engine should accept 'yes' for yes/no question."""
        next_id, next_q, fix, err = engine.process_answer(
            "RDR-CONN-001",
            "q1_phone_works",
            "yes"
        )
        assert err is None
        assert next_q is not None
        assert next_q.id == "q2_check_switch"

    def test_yes_no_answer_no(self, engine):
        """Engine should accept 'no' for yes/no question."""
        next_id, next_q, fix, err = engine.process_answer(
            "RDR-CONN-001",
            "q1_phone_works",
            "no"
        )
        assert err is None
        assert fix is not None
        assert next_id == "escalate_jack_faulty"

    def test_yes_no_variations(self, engine):
        """Engine should accept common yes/no variations."""
        for answer in ["YES", "Yes", "y", "true", "1", "correct"]:
            next_id, next_q, fix, err = engine.process_answer(
                "RDR-CONN-001",
                "q1_phone_works",
                answer
            )
            assert err is None

    def test_invalid_answer(self, engine):
        """Engine should reject invalid answers."""
        next_id, next_q, fix, err = engine.process_answer(
            "RDR-CONN-001",
            "q1_phone_works",
            "maybe"
        )
        assert err is not None
        # Error should mention expected yes/no for this question type
        assert ("expected" in err.lower() or "not recognized" in err.lower())

    def test_nonexistent_rule(self, engine):
        """Engine should fail gracefully for unknown rule."""
        next_id, next_q, fix, err = engine.process_answer(
            "RDR-FAKE-999",
            "q1",
            "yes"
        )
        assert err is not None
        assert "Rule not found" in err


class TestDecisionPaths:
    """Test complete decision paths through rules."""

    def test_rdr_conn_001_path_physical_cable(self, engine):
        """Walk through RDR-CONN-001 physical cable path."""
        # Q1: Is phone working? YES
        next_id, next_q, fix, _ = engine.process_answer("RDR-CONN-001", "q1_phone_works", "yes")
        assert next_q.id == "q2_check_switch"

        # Q2: Is MAC in switch table? NO
        next_id, next_q, fix, _ = engine.process_answer("RDR-CONN-001", "q2_check_switch", "no")
        assert next_q.id == "q3_cable_swap"

        # Q3: Does swap work? YES
        next_id, next_q, fix, _ = engine.process_answer("RDR-CONN-001", "q3_cable_swap", "yes")
        assert fix is not None
        assert "Reseat" in fix.title

    def test_rdr_conn_001_path_jack_fault(self, engine):
        """Walk through RDR-CONN-001 jack fault path."""
        # Q1: Is phone working? NO → escalate_jack_faulty
        next_id, next_q, fix, _ = engine.process_answer("RDR-CONN-001", "q1_phone_works", "no")
        assert fix is not None
        assert "jack" in fix.title.lower()


class TestRuleMetadata:
    """Test rule metadata and tagging."""

    def test_rule_has_tags(self, engine):
        """Rules should have relevant tags."""
        rule = engine.get_rule("RDR-CONN-001")
        assert len(rule.tags) > 0
        assert "physical_layer" in rule.tags

    def test_rule_references_graph(self, engine):
        """Rules should document which graph entities they query."""
        rule = engine.get_rule("RDR-CONN-002")
        assert rule.graph_references is not None
        assert len(rule.graph_references) > 0

    def test_recurring_patterns(self, engine):
        """Some rules should be marked as recurring."""
        rule = engine.get_rule("RDR-ACCESS-001")
        assert rule.recurrence >= 2, "Promotion/AD group rule should be recurring"


class TestEscalation:
    """Test escalation paths."""

    def test_escalation_fix_exists(self, engine):
        """All escalation branches should reference valid fixes."""
        for rule_id, rule in engine.rules.items():
            for question in rule.questions:
                for destination in question.branches.values():
                    if destination.startswith("escalate_"):
                        assert destination in rule.fixes, \
                            f"Escalation fix '{destination}' not defined in {rule_id}"

    def test_escalation_confidence_low(self, engine):
        """Escalation fixes should have lower confidence."""
        rule = engine.get_rule("RDR-CONN-002")
        escalate_fix = rule.fixes.get("escalate_firewall")
        assert escalate_fix is not None
        assert escalate_fix.confidence < 0.8, "Escalations should have lower confidence"


class TestLearnedRules:
    """Test the capability to suggest and create learned rules."""

    def test_suggest_learned_rule(self, engine):
        """Engine should propose a new rule from operator findings."""
        learned = engine.suggest_learned_rule(
            "RDR-CONN-001",
            "Pigtail was crimped, not loose",
            "Replace daisy-chain pigtail",
            ["Order new pigtail", "Replace connector"],
            confidence=0.85
        )
        
        assert learned is not None
        assert "learned" in learned.name.lower()
        assert learned.confidence == 0.85
        assert "Replace" in learned.fix_title


class TestConversationState:
    """Test conversation state tracking."""

    def test_state_creation(self):
        """ConversationState should initialize properly."""
        state = ConversationState(
            session_id="test-001",
            rule_id="RDR-CONN-001",
            current_question_id="q1_phone_works"
        )
        
        assert state.rule_id == "RDR-CONN-001"
        assert state.status == "in_progress"
        assert len(state.operator_answers) == 0

    def test_state_recording_answers(self):
        """State should track operator answers."""
        state = ConversationState(
            session_id="test-001",
            rule_id="RDR-CONN-001",
            current_question_id="q1_phone_works"
        )
        
        state.operator_answers["q1_phone_works"] = "yes"
        state.path_taken.append("q1_phone_works")
        
        assert state.operator_answers["q1_phone_works"] == "yes"
        assert len(state.path_taken) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
