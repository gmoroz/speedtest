# Версии линтеров workflow закреплены точно: uvx качает их по пину при первом запуске.
ACTIONLINT_VERSION := 1.7.12.25
ZIZMOR_VERSION := 1.30.1

LINT_TARGETS += ci-lint
CODE_CHECKS += ci
ci_CODE_PATHS := .github
ci_CODE_FORMAT_TARGETS :=
ci_CODE_LINT_TARGETS := ci-lint
ci_CODE_TEST_TARGETS :=
ROOT_ALLOWED += .github .copier-answers-ci.yml

.PHONY: ci-lint

ci-lint: ## Проверить GitHub Actions workflow: actionlint, zizmor и контракт
	@set -euo pipefail; \
	workflows=$$(git ls-files --cached --others --exclude-standard -- '.github/workflows/*.yml' '.github/workflows/*.yaml'); \
	printf '%s\n' "$$workflows" | xargs uvx --from "actionlint-py==$(ACTIONLINT_VERSION)" actionlint -color; \
	uvx "zizmor==$(ZIZMOR_VERSION)" --offline --pedantic .github/workflows/; \
	bash .github/scripts/check_workflow_contract.sh; \
	bash .github/scripts/check_node_package_json.sh >/dev/null; \
	printf 'ci-lint: OK\n'
