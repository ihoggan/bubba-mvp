# Bubba MVP — RDR Troubleshooting Engine

A working prototype of the Unified IT Brain's core RDR (Ripple Down Rules) troubleshooting layer. This MVP proves the concept: **guided troubleshooting + in-the-moment learning**.

## What is This?

Bubba is an AI-powered troubleshooting assistant for IT technicians. This MVP focuses on the **RDR engine**—a decision-tree system that:

1. **Guides** an operator through diagnostic questions
2. **Branches** on answers, isolating the problem
3. **Escalates** when confidence is low or data is unavailable
4. **Learns** when the operator finds something the rules didn't predict

**Why RDR?** Traditional ML needs retraining; RDR grows incrementally. Each new ticket teaches it without touching the model.

## Quick Start

### Installation

```bash
cd bubba-mvp
uv sync  # or: pip install -e ".[dev]"
```

### Run the CLI

```bash
# List all rules
python main.py list

# Search for rules
python main.py search connectivity

# Start troubleshooting with a specific rule
python main.py start RDR-CONN-001

# See available commands
python main.py --help
```

### Example Session

```
$ python main.py start RDR-CONN-001

==================================================
  Single endpoint no link - daisy chain issue
==================================================

User PC has no internet but VoIP phone works fine on same jack.

Q1: Does the VoIP phone on the same jack work?
💡 If phone is fine, the jack and main cable are OK. Isolates to the PC end.
Your answer [yes/no]: yes

Q2: Check the switch port. Is the PC's MAC address in the MAC table?
Your answer [yes/no]: no

Q3: Swap the patch cable between phone and PC. Does PC get DHCP?
Your answer [yes/no]: yes

✓ Resolution:
Reseat the daisy-chain cable

  → Unplug the PC-side pigtail connector completely
  → Reseat it firmly until the clip locks with an audible click
  → Verify DHCP lease on PC (run ipconfig /all)
  → Confirm access to network resources (ping gateway, open CRM)
  → Monitor for 5 minutes; if stable, close ticket

Confidence: 95%

Did this fix resolve the issue? [Y/n]: y
✓ Excellent! Glad we could help.

==================================================
Session Complete
Status: completed | Rule: RDR-CONN-001
Questions: 3 | Session: session-2026-09-09T...
==================================================
```

## Architecture

### Files

```
bubba-mvp/
├── data/
│   ├── rdr_rules.json          # 8 extracted rules from seed tickets
│   └── sessions/               # Audit trail of all sessions
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic models: Rule, Question, Fix, etc.
│   ├── engine.py              # RDR engine: loads rules, handles branching
│   └── cli.py                 # (legacy; see main.py instead)
├── tests/
│   └── test_engine.py         # Comprehensive test suite
├── main.py                    # Typer CLI entry point
├── pyproject.toml            # uv/pip configuration
└── README.md                 # This file
```

### Data Flow

```
┌─ RDR Rules (JSON) ───────────────────┐
│  8 extracted rules from seed tickets │
│  (T101, T102, T103, T109, T111,      │
│   T123, T125, T118)                  │
└──────────────────┬────────────────────┘
                   │
                   ▼
         ┌─ RDREngine ─────────────────┐
         │ • Load & index rules        │
         │ • Sequence questions        │
         │ • Process answers           │
         │ • Branch on results         │
         └────────────┬────────────────┘
                      │
                      ▼
         ┌─ CLI (Typer + Rich) ────────┐
         │ • Display questions         │
         │ • Collect operator input    │
         │ • Show resolutions          │
         │ • Capture new findings      │
         └────────────┬────────────────┘
                      │
                      ▼
         ┌─ Session Log (JSON) ────────┐
         │ • Audit trail               │
         │ • Learned rules             │
         │ • Operator feedback         │
         └─────────────────────────────┘
```

## Rules Extracted

**8 RDR rules** extracted from the 25 seed tickets, representing the most common and highest-value troubleshooting patterns:

| Rule ID | Name | Category | Tickets | Learning Value |
|---------|------|----------|---------|-----------------|
| RDR-CONN-001 | Single endpoint no link | connectivity | T101 | Physical layer isolation |
| RDR-CONN-002 | Multi-user outage | connectivity | T102 | LAG/topology-aware |
| RDR-CONN-003 | Jack label mismatch | connectivity | T103 | Infrastructure discovery |
| RDR-CONN-004 | Conference cable unplugged | connectivity | T109, T118 | Recurring user error |
| RDR-VOICE-001 | VoIP registration failure | voice_and_video | T111 | VLAN config drift |
| RDR-ACCESS-001 | AD group after promotion | access_and_accounts | T123 | Recurring (4x), escalation |
| RDR-CABLE-001 | Cable unseated at desk | connectivity | T118 | Recurring, quick fix |
| RDR-EDGE-001 | Open ticket edge case | voice_and_video | T125 | Escalation pattern |

Each rule includes:
- **Decision tree**: Questions → branching logic
- **Resolutions**: Fixes with step-by-step instructions
- **Escalations**: When confidence is low
- **Graph references**: Which topology entities to query
- **Metadata**: Tags, recurrence count, preventive actions

## Test Coverage

Run the test suite:

```bash
pytest tests/ -v
```

Tests cover:
- ✓ Rule loading and retrieval
- ✓ Question sequencing
- ✓ Answer processing (yes/no, choice, open)
- ✓ Complete decision paths (e.g. physical cable isolation)
- ✓ Escalation handling
- ✓ Learned rule creation
- ✓ Conversation state tracking

## Design Decisions

### Why Python-only?

Single language, single dependency manager, single test runner. Easier to hand off to the next engineer. See ADR 0002.

### Why RDR, not ML?

RDR grows without retraining. Each operator fixes something Bubba doesn't know, and Bubba captures it as a new rule—synchronously, in the moment, without data science. See ADR 0001.

### Why these 8 rules?

Extracted from 25 seed tickets. These 8 cover:
- Physical layer issues (most common)
- Topology-aware reasoning (LAG, VLAN, inter-rack)
- Recurring patterns (cable, AD group)
- Escalation (when data unavailable)
- Edge cases (open tickets, third-party deps)

The pattern: **high recurrence → high value**.

### Why JSON for rules?

Structured, versioned, portable. Easy to version-control, audit, and evolve. No DSL to learn; just shape rules as data.

## What's Next?

### Phase 2: Vector DB
Embed past tickets. "Have we seen this before?" capability. Similarity search for edge cases.

### Phase 3: Graph Layer  
Topology as a first-class data structure. "Where in the network?" answers. RDR rules can query the graph.

### Phase 4: Integration
Compose vector + graph + RDR. Confidence scoring across layers. Escalation when disagreement.

### Phase 5: API & UI
FastAPI service. CLI becomes HTTP client. Web UI for non-technical operators.

### Phase 6: Discovery
Real-world data ingestion. MAC tables, DHCP, AD dumps, photographs of labels. Topology construction from evidence, not authored JSON.

## Roadmap Exit Criteria

**MVP is done when:**
- ✓ 8 rules extracted from tickets and working
- ✓ RDR engine sequences questions, branches, escalates
- ✓ CLI guides operator start-to-finish
- ✓ Session state captured for audit
- ✓ Learned rules can be proposed
- ✓ Test suite covers core paths

**All of the above are complete.** The MVP is ready for:
1. In-session testing (your own troubleshooting)
2. Feedback loop validation (does learning work?)
3. Operator UX polish (is the CLI natural?)
4. Integration with topology graph (Phase 3)

## Key Insights

### RDR is a Feedback Loop, Not a Classifier

Traditional ML: Train on data → model → predictions.  
**RDR:** Rule fires → operator corrects → new rule added → smarter next time.

This is a **live system** that learns in real time.

### Confidence Matters More Than Accuracy

We don't try to be right 100% of the time. We:
1. Give our best guess with a confidence score
2. Escalate when confidence is low
3. Learn when we're wrong
4. Get smarter over time

### Topology is Context, Not an Afterthought

Rules that say "check the switch port" are better than rules that say "check the network." The topology graph is how Bubba understands *where* the problem lives.

## Development Notes

### Adding a New Rule

1. Extract the decision tree from a ticket
2. Write it as JSON in `data/rdr_rules.json`
3. Use the template in `data/rdr_rules.json` as a guide
4. Run tests to ensure all branches are valid

### Modifying the Engine

The engine is intentionally simple. It:
- Loads rules from JSON
- Indexes them by ID
- Sequences questions
- Handles branching
- Captures escalations

Don't add complexity. If you find yourself doing something clever, question whether it belongs in RDR at all (it might belong in the graph layer or vector layer instead).

### Testing a Session Manually

```bash
python main.py start RDR-CONN-001
# Answer questions...
# Session saved to data/sessions/

# Review session
cat data/sessions/session-*.json | jq .
```

## Known Limitations

1. **No topology context yet.** Rules can reference graph entities, but the graph isn't loaded. Phase 3 adds this.
2. **No vector search.** Can't find similar past tickets. Phase 2 adds this.
3. **No persistence of learned rules.** Learned rules are proposed but need manual curation to make into official rules.
4. **No multi-session state.** Each session is independent. Phase 4 adds session history.

These are not bugs; they're **intentional deferred decisions**. Each layer builds on what comes before.

## References

- **ADR 0001**: Three-layer architecture (vector + graph + RDR)
- **ADR 0002**: Python-only stack
- **ADR 0003**: Topology as teaching instrument
- **ADR 0004**: Bubba's Sandbox vs. Production

See `../docs/adr/` in the parent Bubba project for full context.

## Questions?

This MVP is designed to be **self-documenting code**. Read the rules in `data/rdr_rules.json`, the models in `src/models.py`, and the engine in `src/engine.py`. Each is commented and structured for clarity.

The test suite (`tests/test_engine.py`) is an executable specification of how the engine works.

---

**Status:** MVP complete, ready for field testing.  
**Built:** September 2026  
**For:** Iain Hoggan, IT tech + AI/ML explorer
