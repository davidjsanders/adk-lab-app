.PHONY: install test playground deploy clean

install:
	uv venv .venv
	PIP_EXTRA_INDEX_URL="https://pypi.org/simple" uv pip install -r requirements.txt pytest --python .venv

test:
	PYTHONPATH=. .venv/bin/pytest tests/

playground:
	PYTHONPATH=. .venv/bin/adk web .

deploy:
	./deploy.sh

clean:
	rm -rf .venv __pycache__ tests/__pycache__
