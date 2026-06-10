.PHONY: verify verify-web verify-api

verify:
	./scripts/verify.sh

verify-web:
	npm -C apps/web run lint && npm -C apps/web run build

verify-api:
	python3 -m pytest -q
