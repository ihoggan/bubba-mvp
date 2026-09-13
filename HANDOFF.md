# Bubba Phase A→B Handoff

## Status
- Phase A (Investigation Lifecycle UI) ✅ Complete
- Backend fully functional and tested (53 tests)
- Streamlit prototype working but not ideal for state-heavy workflows
- Decision: Migrate to PyQt desktop app

## What Transfers Unchanged

Backend only:
- Domain models: bubba/diagnosis/domain/
- Repository & serializer: bubba/diagnosis/infrastructure/
- FastAPI: bubba/diagnosis/api/
- Tests: tests/
- Database schema

Only UI changes:
- Remove: bubba/diagnosis/web/ (Streamlit)
- Create: bubba/diagnosis/desktop/ (PyQt)

## Development Environment

```bash
cd ~/bubba-mvp
source venv/bin/activate
pip install PyQt6
python -m pytest tests/ -v
```

## Next Task: PyQt Desktop App (4-5h)

Windows to build:
1. MainWindow — Navigation menu
2. NewInvestigationDialog — 2-step form
3. EditInvestigationWindow — 5 tabs
4. SearchResultsWindow — Keyword search
5. DetailViewWindow — Full investigation + export

## Success Criteria

✅ PyQt app launches  
✅ Create investigation → saves to DB  
✅ Edit loads real data  
✅ Search works  
✅ View shows investigation  
✅ Export produces JSON  
✅ All 53 tests pass  

