# Bubba.Diagnosis

Structured incident investigation module for Bubba. Evidence-driven diagnosis with ordinal confidence levels and immutable investigation timelines.

## Role in Bubba

**Bubba.Diagnosis** is an escalation path for complex incidents:

1. **Bubba core** triages tickets and suggests initial troubleshooting paths
2. **Complex incidents** escalate to Bubba.Diagnosis for structured investigation
3. **Diagnosis confirmed** with full evidence provenance and causal chain
4. **Verified incidents** export as KB entries back into Bubba's learning loop

## Architecture

```
Streamlit UI -> FastAPI -> Application Services -> Domain -> SQLAlchemy/SQLite
                                      |
                                      +-> Deterministic reasoning engine
```

The domain layer has zero framework dependencies. The reasoning engine is deterministic and explainable.

## Core concepts

**Epistemic types:**
- FACT: stable statement established independently
- OBSERVATION: directly observed during a test
- ASSUMPTION: explicitly unverified premise
- HYPOTHESIS: candidate explanation
- INFERENCE: interpretation derived from observations
- CONCLUSION: engineer-confirmed outcome

**Confidence levels (ordinal, not probabilistic):**
```
UNASSESSED -> VERY_WEAK -> WEAK -> PLAUSIBLE -> STRONG -> VERY_STRONG -> CONFIRMED/RULED_OUT
```

**Key separation:** Diagnosis (causal explanation) is tracked independently from remediation (intervention). A failed remediation does not invalidate a correct diagnosis.

## Run locally

### Option A: Virtual environment

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
```

Run the API:
```bash
uvicorn bubba.diagnosis.api.main:app --reload
```

In another terminal, run the UI:
```bash
streamlit run bubba/diagnosis/web/app.py
```

Open http://localhost:8501 in your browser.

### Run tests

```bash
pytest -q
```

## Synthetic demo

The UI includes a seeded scenario demonstrating the full reasoning pattern:

1. Apparent application/network communication failure
2. Connectivity evidence weakens network-path hypotheses
3. Process/event evidence strengthens application-control hypothesis
4. Policy remediation is attempted
5. Application remains blocked
6. System does NOT automatically downgrade the diagnosis
7. Remediation branch investigated separately, reveals management-context failure
8. Verification confirms corrected policy state and successful application behaviour

## Non-goals for this MVP

- No autonomous system changes
- No PowerShell execution
- No production integrations
- No probabilistic diagnosis claims
- No machine-learning model
- No automatic promotion of incidents into KB guidance

## Safety / operational boundary

This module is advisory. It generates structured investigation records with full evidence provenance. Consequential actions remain human-controlled.
