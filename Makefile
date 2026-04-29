.PHONY: run lint check docker-up docker-down

run:
	uvicorn src.main:app --reload --port 8000

check:
	python -m py_compile src/main.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
