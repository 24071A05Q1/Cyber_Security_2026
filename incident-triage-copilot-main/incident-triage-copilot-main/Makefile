bootstrap:
	python scripts/bootstrap.py

api:
	uvicorn app.api:app --reload

dashboard:
	streamlit run app/dashboard.py

evaluate:
	python -m src.evaluation.evaluate

test:
	pytest -q
