#!/usr/bin/env bash
# Одна строка engines.node и один packageManager во всех package.json: setup-node/pnpm ставят один рантайм.
set -euo pipefail

package_file=""
node_spec=""
package_manager=""

while IFS= read -r -d '' manifest; do
	case "$manifest" in
		node_modules/*|*/node_modules/*) continue ;;
		# Локальный npm-инструментарий core (jscpd), не рантайм кубика: npm ci, не pnpm.
		scripts/package.json) continue ;;
	esac
	node_here=$(jq -r 'if (.engines.node | type) == "string" then .engines.node else empty end' "$manifest")
	if [ -z "$node_here" ]; then
		printf 'В %s поле engines.node пустое или отсутствует\n' "$manifest" >&2
		exit 1
	fi
	manager_here=$(jq -r 'if (.packageManager | type) == "string" then .packageManager else empty end' "$manifest")
	if [ -z "$manager_here" ]; then
		printf 'В %s поле packageManager пустое или отсутствует\n' "$manifest" >&2
		exit 1
	fi
	if [ -z "$package_file" ]; then
		package_file=$manifest
		node_spec=$node_here
		package_manager=$manager_here
		continue
	fi
	if [ "$node_here" != "$node_spec" ]; then
		printf 'Ожидалась одна строка engines.node во всех package.json.\n%s: %s\n%s: %s\n' \
			"$package_file" "$node_spec" "$manifest" "$node_here" >&2
		exit 1
	fi
	if [ "$manager_here" != "$package_manager" ]; then
		printf 'Ожидался один packageManager во всех package.json.\n%s: %s\n%s: %s\n' \
			"$package_file" "$package_manager" "$manifest" "$manager_here" >&2
		exit 1
	fi
done < <(git ls-files -z -- ':(glob)**/package.json')

# Нет package.json — сверка не нужна (python-cli и прочие без Node).
if [ -z "$package_file" ]; then
	exit 0
fi

printf '%s\n' "$package_file"
