.PHONY: verify verify-web verify-api dev api web

verify:
	./scripts/verify.sh

verify-web:
	npm -C apps/web run lint && npm -C apps/web run build

verify-api:
	python3 -m pytest -q

dev:
	./scripts/dev.sh

api:
	./scripts/start-api.sh

web:
	./scripts/start-web.sh
