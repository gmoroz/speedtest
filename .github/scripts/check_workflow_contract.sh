#!/usr/bin/env bash
# Инвариант check.yml: make install/full-check и CARGO_INCREMENTAL; без обходов CI.
set -euo pipefail

check_yml=".github/workflows/check.yml"
if [ ! -f "$check_yml" ]; then
	printf 'Нет %s: workflow кубика ci обязателен\n' "$check_yml" >&2
	exit 1
fi

# Только исполняемый run:-шаг целиком, без хвоста и комментария в той же строке.
require_run_step() {
	local command="$1"
	local pattern="^[[:space:]]*(-[[:space:]]+)?run:[[:space:]]+${command}[[:space:]]*$"
	if ! grep -qE -- "$pattern" "$check_yml"; then
		printf '%s: нет шага `run: %s` (строка целиком)\n' "$check_yml" "$command" >&2
		exit 1
	fi
}

require_run_step 'make install'
require_run_step 'make full-check'

if ! grep -qE -- '^[[:space:]]*CARGO_INCREMENTAL[[:space:]]*:' "$check_yml"; then
	printf '%s: нет ключа CARGO_INCREMENTAL\n' "$check_yml" >&2
	exit 1
fi

workflows=$(git ls-files --cached --others --exclude-standard -- \
	'.github/workflows/*.yml' '.github/workflows/*.yaml')
if [ -z "$workflows" ]; then
	printf 'В .github/workflows/ нет отслеживаемых workflow\n' >&2
	exit 1
fi

while IFS= read -r workflow; do
	[ -n "$workflow" ] || continue
	# YAML-ключ после отступа, опционально как элемент списка (- key:).
	# Упоминание в комментарии (# ...) не считается.
	if grep -qE -- '^[[:space:]]*(-[[:space:]]+)?continue-on-error[[:space:]]*:' "$workflow"; then
		printf '%s: запрещён continue-on-error\n' "$workflow" >&2
		exit 1
	fi
	# Ключ-форма и списочная форма on: [push, pull_request_target].
	if grep -qE -- '^[[:space:]]*(-[[:space:]]+)?pull_request_target[[:space:]]*:' "$workflow" \
		|| grep -qE -- '^[[:space:]]*(-[[:space:]]+)?on:[[:space:]]*\[[^]#]*\bpull_request_target\b' "$workflow"; then
		printf '%s: запрещён pull_request_target\n' "$workflow" >&2
		exit 1
	fi
	if grep -qE -- '^[[:space:]]*(-[[:space:]]+)?if:[[:space:]]*['\''"]?false\b' "$workflow"; then
		printf '%s: запрещён if: false\n' "$workflow" >&2
		exit 1
	fi
done <<< "$workflows"
