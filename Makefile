.PHONY: install validate test fmt terraform-validate

install:
	python -m pip install -e '.[dev]'

validate:
	python scripts/validate_repo.py .
	python -m ruff check scripts tests
	python -m pytest -q

fmt:
	python -m ruff format scripts tests
	terraform -chdir=terraform fmt -recursive

terraform-validate:
	terraform -chdir=terraform init -backend=false
	terraform -chdir=terraform validate
