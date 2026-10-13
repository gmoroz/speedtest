.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash

INSTALL_TARGETS :=
FORMAT_TARGETS :=
LINT_TARGETS := check-root check-file-lines check-no-skips check-no-markers check-agents check-jscpd
TEST_TARGETS :=
CODE_CHECKS :=
CORE_CODE_PATHS := Makefile mk scripts .githooks
ROOT_ALLOWED := .copier-answers-core.yml
CODE_FILE_LIMIT := 400
TEST_FILE_LIMIT := 800
JSCPD_VERSION := 5.3.3
# Cargo-инструменты Rust-кубиков ставятся в общий ~/.cargo/bin, поэтому версия у всех одна
# (scripts/install_cargo_tools.sh): разные версии в кубиках переустанавливали бы друг друга.
CARGO_DENY_VERSION := 0.20.2
CARGO_MACHETE_VERSION := 0.9.2
CARGO_NEXTEST_VERSION := 0.9.146
CARGO_LLVM_COV_VERSION := 0.9.1
# Личные артефакты инструментов агента: локальный info/exclude, не трекаемый .gitignore.
# Шаблоны без ведущего /: проект может лежать в подкаталоге чужого репозитория.
LOCAL_TOOL_EXCLUDES := .serena/ .playwright-mcp/

# Ответы copier читаются при make, не через Jinja _external_data: copier update рендерит
# шаблон в пустой temp без answers соседей, и подставленное имя вышло бы пустым.
# Отсутствующий файл даёт пустую строку: кубик сам решает, ошибка это или нет.
read_answer = $(shell if [ -f '$(1)' ]; then sed -n 's/^$(2):[[:space:]]*//p' '$(1)' | head -n 1 | tr -d "\r\"'"; fi)
PROJECT_NAME := $(call read_answer,.copier-answers-core.yml,project_name)

-include mk/*.mk

CODE_CHECK_FORMAT_TARGETS := $(foreach code_check,$(CODE_CHECKS),$($(code_check)_CODE_FORMAT_TARGETS))
CODE_CHECK_LINT_TARGETS := $(foreach code_check,$(CODE_CHECKS),$($(code_check)_CODE_LINT_TARGETS))
CODE_CHECK_TEST_TARGETS := $(foreach code_check,$(CODE_CHECKS),$($(code_check)_CODE_TEST_TARGETS))
PROJECT_FORMAT_TARGETS := $(filter-out $(CODE_CHECK_FORMAT_TARGETS),$(FORMAT_TARGETS))
PROJECT_LINT_TARGETS := $(filter-out $(CODE_CHECK_LINT_TARGETS),$(LINT_TARGETS))
PROJECT_TEST_TARGETS := $(filter-out $(CODE_CHECK_TEST_TARGETS),$(TEST_TARGETS))

ifneq ($(FULL_CHECK_FORMATTED),1)
define add_code_check_format_dependencies
$($(1)_CODE_LINT_TARGETS): $($(1)_CODE_FORMAT_TARGETS)
endef
$(foreach code_check,$(CODE_CHECKS),$(eval $(call add_code_check_format_dependencies,$(code_check))))
endif

.PHONY: install format lint test full-check pre-commit-check push help e2e-test-complete \
	$(INSTALL_TARGETS) $(FORMAT_TARGETS) $(LINT_TARGETS) $(TEST_TARGETS)

help: ## Показать доступные команды
	@grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

install: $(INSTALL_TARGETS) ## Подключить git hooks и локальные exclude инструментов
	@git config core.hooksPath .githooks
	@set -euo pipefail; \
	exclude_file="$$(git rev-parse --git-path info/exclude)"; \
	mkdir -p "$$(dirname "$$exclude_file")"; \
	touch "$$exclude_file"; \
	if [ -s "$$exclude_file" ] && [ -n "$$(tail -c 1 "$$exclude_file")" ]; then printf '\n' >> "$$exclude_file"; fi; \
	for pattern in $(LOCAL_TOOL_EXCLUDES); do \
		grep -qxF "$$pattern" "$$exclude_file" || printf '%s\n' "$$pattern" >> "$$exclude_file"; \
	done
	@npm ci --ignore-scripts --prefix scripts
	@printf 'Git hooks подключены, локальные exclude инструментов обновлены.\n'

format: $(FORMAT_TARGETS) ## Отформатировать код

lint: format ## Отформатировать код и выполнить быстрые проверки
	@$(MAKE) --no-print-directory FULL_CHECK_FORMATTED=1 $(LINT_TARGETS)

test: $(TEST_TARGETS) ## Выполнить тесты

# Барьер пуст без кубика e2e; deploy-smoke ждёт завершения e2e, если он есть.
e2e-test-complete:

# Тот же селектор, что full-check: индекс вместо diff с upstream, без тестов.
pre-commit-check: ## Format/lint по файлам индекса (хук pre-commit)
	@CHANGED_SCOPE=cached RUN_TESTS=0 CHECK_LABEL=pre-commit bash scripts/full_check.sh "" "" "$(CORE_CODE_PATHS)" \
		"$(PROJECT_FORMAT_TARGETS)" "$(PROJECT_LINT_TARGETS)" "$(PROJECT_TEST_TARGETS)" \
		$(foreach code_check,$(CODE_CHECKS),--code-check "$(code_check)" "$($(code_check)_CODE_PATHS)" "$($(code_check)_CODE_FORMAT_TARGETS)" "$($(code_check)_CODE_LINT_TARGETS)" "$($(code_check)_CODE_TEST_TARGETS)")

full-check: ## Выполнить проверки изменённого кода и сохранить проверенный SHA
	@bash scripts/full_check.sh "$(FULL)" "$(CI)" "$(CORE_CODE_PATHS)" \
		"$(PROJECT_FORMAT_TARGETS)" "$(PROJECT_LINT_TARGETS)" "$(PROJECT_TEST_TARGETS)" \
		$(foreach code_check,$(CODE_CHECKS),--code-check "$(code_check)" "$($(code_check)_CODE_PATHS)" "$($(code_check)_CODE_FORMAT_TARGETS)" "$($(code_check)_CODE_LINT_TARGETS)" "$($(code_check)_CODE_TEST_TARGETS)")
	@# Маркер только для чистого дерева: иначе проверенный код не совпадает с коммитом, который уйдёт в push.
	@if [ -n "$$(git status --porcelain)" ]; then \
		printf 'full-check: OK (дерево не чистое, маркер для push не записан)\n'; \
	else \
		git rev-parse HEAD > "$$(git rev-parse --git-dir)/full-check-ok"; \
		printf 'full-check: OK\n'; \
	fi

push: ## Проверить чистоту, при необходимости выполнить full-check и отправить текущую ветку
	@if [ -n "$$(git status --porcelain)" ]; then printf 'push: рабочее дерево не чистое.\n' >&2; exit 1; fi
	@marker="$$(git rev-parse --git-dir)/full-check-ok"; \
	if [ -f "$$marker" ] && [ "$$(< "$$marker")" = "$$(git rev-parse HEAD)" ]; then \
		printf 'push: full-check уже выполнен для HEAD.\n'; \
	else \
		$(MAKE) --no-print-directory full-check; \
	fi
	@# ponytail: remote всегда origin; другой remote -> параметр, когда появится второй.
	@git push --set-upstream origin HEAD

check-root:
	@bash scripts/check_root.sh $(ROOT_ALLOWED)

check-file-lines:
	@bash scripts/check_file_lines.sh $(CODE_FILE_LIMIT) $(TEST_FILE_LIMIT) scripts/file-line-exceptions.txt

check-no-skips:
	@bash scripts/check_no_skips.sh

check-no-markers:
	@bash scripts/check_no_markers.sh

check-agents:
	@bash scripts/check_agents.sh

check-jscpd:
	@bash scripts/check_jscpd.sh $(JSCPD_VERSION)
