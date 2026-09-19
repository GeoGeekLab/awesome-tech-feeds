.PHONY: check compile probe

check:
	ruff check .
	ruff format --check .
	mypy
	techfeeds validate
	techfeeds compile --check
	pytest

compile:
	techfeeds compile

probe:
	techfeeds probe --concurrency 8
