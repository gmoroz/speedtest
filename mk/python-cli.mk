PYTHON_CLI_DIR := speedtest

INSTALL_TARGETS += python-cli-install
FORMAT_TARGETS += python-cli-format
LINT_TARGETS += python-cli-lint
TEST_TARGETS += python-cli-test
CODE_CHECKS += python-cli
python-cli_CODE_PATHS := $(PYTHON_CLI_DIR)
python-cli_CODE_FORMAT_TARGETS := python-cli-format
python-cli_CODE_LINT_TARGETS := python-cli-lint
python-cli_CODE_TEST_TARGETS := python-cli-test
ROOT_ALLOWED += speedtest .copier-answers-python-cli.yml

.PHONY: python-cli-install python-cli-format python-cli-lint python-cli-test

python-cli-install: ## Установить Python CLI-зависимости через uv
	@cd "$(PYTHON_CLI_DIR)" && uv sync --locked --group dev

python-cli-format: ## Отформатировать Python CLI-код
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked ruff check --fix src tests
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked ruff format src tests

python-cli-lint: ## Проверить Python CLI: ruff, mypy, vulture, import-linter, uv lock
	@cd "$(PYTHON_CLI_DIR)" && uv lock --check
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked ruff check src tests
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked ruff format --check src tests
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked mypy src tests
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked vulture src vulture_whitelist.py
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked lint-imports

python-cli-test: ## Прогнать тесты Python CLI с coverage
	@cd "$(PYTHON_CLI_DIR)" && uv run --locked pytest
