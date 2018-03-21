all: check

check:
	@scripts/check.py $$(find . -name "*.yaml")
