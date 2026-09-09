"""
RDR (Ripple Down Rules) Engine.
Loads rules, manages question sequences, handles branching and escalations.
"""

import json
from pathlib import Path
from typing import Optional, Tuple
from src.models import Rule, ConversationState, Question, Fix, LearnedRule


class RDREngine:
    """Interprets RDR rules to guide operator troubleshooting."""

    def __init__(self, rules_file: Path):
        """Load rules from JSON file."""
        self.rules: dict[str, Rule] = {}
        self.load_rules(rules_file)

    def load_rules(self, rules_file: Path):
        """Load all rules from JSON file, validate, index by rule_id."""
        with open(rules_file) as f:
            raw_rules = json.load(f)
        
        for rule_data in raw_rules:
            rule = Rule(**rule_data)
            self.rules[rule.rule_id] = rule
            print(f"  Loaded {rule.rule_id}: {rule.name}")

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Retrieve a rule by ID."""
        return self.rules.get(rule_id)

    def get_first_question(self, rule_id: str) -> Optional[Question]:
        """Get the entry-point question for a rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        # Find the question matching the entry_point ID
        for q in rule.questions:
            if q.id == rule.entry_point:
                return q
        return None

    def get_question(self, rule_id: str, question_id: str) -> Optional[Question]:
        """Retrieve a specific question by rule and question ID."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        
        for q in rule.questions:
            if q.id == question_id:
                return q
        return None

    def process_answer(
        self, 
        rule_id: str, 
        question_id: str, 
        answer: str
    ) -> Tuple[str, Optional[Question], Optional[Fix], Optional[str]]:
        """
        Process an operator's answer and return the next step.
        
        Returns:
            (next_id, next_question, fix_if_complete, escalation_if_applicable)
            where next_id is either a question_id, fix_id, or "escalate"
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return ("escalate", None, None, "Rule not found")

        question = self.get_question(rule_id, question_id)
        if not question:
            return ("escalate", None, None, "Question not found")

        # Normalize answer based on question type
        normalized_answer = answer.strip().lower()

        # For yes_no questions, handle common variations
        if question.type.value == "yes_no":
            if normalized_answer in ("yes", "y", "true", "1", "correct", "ok"):
                normalized_answer = "yes"
            elif normalized_answer in ("no", "n", "false", "0", "incorrect", "nope"):
                normalized_answer = "no"
            else:
                return ("escalate", None, None, f"Expected yes/no, got: {answer}")

        # Look up where this answer branches to
        if normalized_answer not in question.branches:
            return ("escalate", None, None, f"Answer '{answer}' not recognized for this question")

        next_id = question.branches[normalized_answer]

        # Determine what the next_id refers to
        # It could be another question ID, a fix ID, or "escalate"
        
        if next_id == "escalate":
            return ("escalate", None, None, f"Rule {rule_id} requires escalation at this point")

        # Try to find it as a question
        next_question = self.get_question(rule_id, next_id)
        if next_question:
            return (next_id, next_question, None, None)

        # Try to find it as a fix
        if next_id in rule.fixes:
            fix = rule.fixes[next_id]
            return (next_id, None, fix, None)

        # Try to find it as a fix with "escalate_" prefix
        if next_id.startswith("escalate_"):
            if next_id in rule.fixes:
                fix = rule.fixes[next_id]
                return (next_id, None, fix, "Escalation path")
            else:
                return ("escalate", None, None, f"Escalation fix '{next_id}' not defined")

        return ("escalate", None, None, f"Next step '{next_id}' is neither question nor fix")

    def suggest_learned_rule(
        self,
        rule_id: str,
        finding: str,
        fix_title: str,
        fix_steps: list[str],
        confidence: float = 0.70
    ) -> LearnedRule:
        """
        When operator hits a dead end, propose a new rule based on their finding.
        """
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        learned = LearnedRule(
            rule_id=f"RDR-USER-{rule_id}-{id(finding)}",
            name=f"{rule.name} (learned: {finding[:40]}...)",
            category=rule.category,
            subcategory=rule.subcategory,
            description=f"User-learned variant of {rule.rule_id}: {finding}",
            finding=finding,
            fix_title=fix_title,
            fix_steps=fix_steps,
            confidence=confidence,
            created_at="2026-09-09T00:00:00Z"  # Placeholder; should use current time
        )
        return learned

    def list_rules_by_category(self, category: str) -> list[Rule]:
        """Find all active rules in a category."""
        return [
            rule for rule in self.rules.values()
            if rule.category == category and rule.status == "active"
        ]

    def find_rules(self, keywords: list[str]) -> list[Rule]:
        """Search rules by keywords in name or tags."""
        results = []
        for rule in self.rules.values():
            if rule.status != "active":
                continue
            
            combined = (rule.name + " " + rule.description + " " + " ".join(rule.tags)).lower()
            if all(kw.lower() in combined for kw in keywords):
                results.append(rule)
        
        return results
