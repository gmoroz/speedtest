#!/usr/bin/env bash
# Ставит закреплённые cargo-подкоманды, если установленная версия не совпадает с пином.
# Аргументы — пары <пакет> <версия>, например cargo-deny 0.20.2 cargo-machete 0.9.2.
set -euo pipefail

if (( $# == 0 || $# % 2 != 0 )); then
	printf 'install_cargo_tools: нужны пары <пакет> <версия>\n' >&2
	exit 2
fi

while (( $# > 0 )); do
	package="$1"
	expected="$2"
	shift 2
	if [[ "$package" != cargo-* ]]; then
		printf 'install_cargo_tools: %s не cargo-подкоманда\n' "$package" >&2
		exit 2
	fi
	actual=""
	if command -v "$package" >/dev/null; then
		# Форматы различаются: "cargo-deny 0.20.2", "0.9.2", "cargo-nextest 0.9.146 (...)".
		actual="$(cargo "${package#cargo-}" --version | head -n 1)"
	fi
	if [[ " $actual " == *" $expected "* ]]; then
		printf '%s\n' "$actual"
		continue
	fi
	cargo install --locked --force "${package}@${expected}"
done
