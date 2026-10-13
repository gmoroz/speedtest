#!/usr/bin/env bash
# Засевает cargo target linked worktree reflink-копией из главного дерева.
# Usage: seed_cargo_target.sh <relative-target-path>
# Пример: seed_cargo_target.sh cli/target
set -euo pipefail

if [ "$#" -ne 1 ]; then
	printf 'seed_cargo_target: usage: %s <relative-target-path>\n' "$(basename "$0")" >&2
	exit 2
fi

rel_target="$1"

if [ -z "$rel_target" ] || [ "$rel_target" != "${rel_target#/}" ]; then
	printf 'seed_cargo_target: нужен относительный путь target, получено %s\n' "$rel_target" >&2
	exit 2
fi

case "$rel_target" in
	*..*)
		printf 'seed_cargo_target: путь не должен содержать ..: %s\n' "$rel_target" >&2
		exit 2
		;;
esac

if ! git_dir="$(git rev-parse --path-format=absolute --git-dir 2>/dev/null)"; then
	printf 'seed_cargo_target: не git-репозиторий\n' >&2
	exit 1
fi
common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"

# Главное дерево: git-dir совпадает с git-common-dir.
if [ "$git_dir" = "$common_dir" ]; then
	exit 0
fi

if [ -e "$rel_target" ]; then
	exit 0
fi

main_tree="$(dirname "$common_dir")"
src="$main_tree/$rel_target"

if [ ! -d "$src" ]; then
	exit 0
fi

parent="$(dirname "$rel_target")"
if [ "$parent" != "." ] && [ ! -d "$parent" ]; then
	printf 'seed_cargo_target: нет каталога %s\n' "$parent" >&2
	exit 1
fi

tmp="$rel_target.seed-$$"
cleanup() {
	rm -rf "$tmp"
}
trap cleanup EXIT

err_file="$(mktemp)"
if ! cp -a --reflink=always "$src" "$tmp" 2>"$err_file"; then
	reason="$(tr '\n' ' ' <"$err_file" | sed 's/[[:space:]]*$//')"
	rm -f "$err_file"
	printf 'seed_cargo_target: засев %s пропущен: reflink недоступен (%s)\n' \
		"$rel_target" "${reason:-ошибка cp}"
	exit 0
fi
rm -f "$err_file"

mv "$tmp" "$rel_target"
trap - EXIT
printf 'seed_cargo_target: засеян %s из %s\n' "$rel_target" "$src"
