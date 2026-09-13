# Phase A → Phase B: Streamlit to PyQt Transition

## What Worked in Phase A
- ✅ Full Investigation domain model
- ✅ SQLite persistence with serialization
- ✅ Export protocol (diagnoses → JSON)
- ✅ Search/query by symptom, root cause
- ✅ Narrative UI wording layer
- ✅ 53 tests

## Why We're Moving to PyQt
Streamlit is optimized for dashboards and data exploration, not form-heavy workflows:
- Form submission causes duplicate saves (re-run chaos)
- Session state is complex and fragile
- Page navigation loses context
- Not designed for multi-window desktop UX
- Limited keyboard workflows

## What Stays the Same
- `bubba/diagnosis/domain/` — Domain models
- `bubba/diagnosis/infrastructure/` — Repository, serializer
- `bubba/diagnosis/api/` — FastAPI (for future Bubba Core integration)
- Database schema
- All tests

## What Changes
- `bubba/diagnosis/web/` — New PyQt app (replaces Streamlit)

## Timeline
- Phase A (Complete): Proof of concept, 3 priorities, working backend
- Phase A→B: Migrate to PyQt (4-5h)
- Phase B: Bubba Core integration (3-4h)

## How to Run Old Streamlit Version
```bash
git checkout phase-a-streamlit
streamlit run bubba/diagnosis/web/app.py
```
