"""Translation layer: convert technical timeline events to incident narrative."""

from bubba.diagnosis.domain.models import Investigation, TimelineEvent


class EventNarrator:
    """Converts technical events into human-readable incident narration."""

    @staticmethod
    def translate_event(event: TimelineEvent) -> str:
        """Convert a technical event into plain language.
        
        Args:
            event: TimelineEvent with type and payload
            
        Returns:
            Human-readable narrative sentence
        """
        event_type = event.event_type
        payload = event.payload or {}
        summary = event.summary
        
        # If the event already has a good summary, use it as-is
        if summary and not summary.startswith("{") and len(summary) > 10:
            return f"✓ {summary}"
        
        # Otherwise, build from event type
        translations = {
            "confidence_updated": lambda p: f"Belief updated: {p.get('hypothesis', 'hypothesis')} is now {p.get('new_belief', 'uncertain')}",
            "diagnostic_test": lambda p: f"Test ran: {p.get('test', 'diagnostic test')}",
            "diagnostic_test_passed": lambda p: f"✓ Test result supports the investigation: {p.get('test', 'test')}",
            "diagnostic_test_failed": lambda p: f"✗ Test ruled out a hypothesis: {p.get('test', 'test')}",
            "remediation_failure_classified": lambda p: f"⚠ Fix attempt failed, but diagnosis holds. Issue: {p.get('failure_mode', 'unclear')}",
            "intervention_executed": lambda p: f"Fix applied: {p.get('intervention', 'intervention')}",
            "intervention_verified": lambda p: f"✓ Service restored — fix verified effective",
            "verification_passed": lambda p: f"✓ Independent verification passed: problem is resolved",
            "root_cause_confirmed": lambda p: f"📌 Root cause locked: {p.get('root_cause', 'root cause established')}",
        }
        
        if event_type in translations:
            return translations[event_type](payload)
        
        # Fallback: use summary as-is
        return f"• {summary or event_type}"

    @staticmethod
    def investigation_narrative(inv: Investigation) -> list[str]:
        """Build a chronological incident narrative from timeline.
        
        Returns:
            List of narrative sentences, one per event
        """
        narrator = EventNarrator()
        narrative = []
        
        for event in inv.timeline:
            narrative.append(narrator.translate_event(event))
        
        return narrative


def evidence_reliability_label(reliability: str) -> str:
    """Convert technical reliability to user-friendly label.
    
    Args:
        reliability: one of "unknown", "low", "medium", "high"
        
    Returns:
        User-friendly label with confidence indicator
    """
    labels = {
        "high": "🔒 Verified",
        "medium": "⚠ Tested",
        "low": "📝 Observed",
        "unknown": "❓ Unverified"
    }
    return labels.get(reliability, "Unverified")


def belief_emoji(belief: str) -> str:
    """Return emoji indicator for belief level.
    
    Args:
        belief: one of BeliefLevel enum values
        
    Returns:
        Emoji + label
    """
    emojis = {
        "confirmed": "✅ Confirmed",
        "very_strong": "💪 Very Strong",
        "strong": "👍 Strong",
        "plausible": "🤔 Plausible",
        "weak": "❓ Weak",
        "very_weak": "❌ Very Weak",
        "ruled_out": "🚫 Ruled Out",
        "unassessed": "⏳ Unassessed"
    }
    return emojis.get(belief, belief)
