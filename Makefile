all: check

check:
	@scripts/check.py $$(find . -name "*.yaml")

incorrects:
	@scripts/incorrects.py $$(find . -name "*.yaml")

install-hook:
	cp -fp scripts/pre-push .git/hooks
