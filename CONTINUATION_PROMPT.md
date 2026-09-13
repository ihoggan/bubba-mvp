# Bubba Phase A→B Continuation Prompt

You are Claude, continuing work on Bubba—a personal IT troubleshooting knowledge engine.

## Current State (2026-09-13, end of Session 2)

- Bubba core RDR engine exists (25 worked tickets, 8 decision trees)
- Bubba.Diagnosis module fully integrated: structured incident investigation with evidence provenance
- Phase 2 (three priorities) COMPLETE
- Phase A: Investigation lifecycle UI COMPLETE with Streamlit
- **DECISION MADE:** Migrate from Streamlit to PyQt desktop app

## Working Agreement

- Provide actual shell commands alongside code
- Test everything, commit frequently
- Stick to the plan sequentially
- Solo technician tool for Iain (UK-based, IT technician)

## Backend (LOCKED DOWN & REUSABLE)

- bubba/diagnosis/domain/ — Investigation model
- bubba/diagnosis/infrastructure/ — Repository, serializer
- bubba/diagnosis/api/ — FastAPI endpoints
- Tests: 53 passing

## Next Immediate Work

Phase A→B: Build PyQt desktop app (4-5h)
- Create bubba/diagnosis/desktop/main.py
- Build windows (New, Edit, View, Search)
- Wire to existing backend
- Test full end-to-end

## Repository State

Main branch, ready for PyQt work
Tag: v0.1-streamlit-prototype (Streamlit archived)
All tests passing
