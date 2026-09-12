.PHONY: install test api ui lint

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

api:
	uvicorn decisiondesk.api.main:app --reload

ui:
	streamlit run src/decisiondesk/web/app.py

lint:
	ruff check .
