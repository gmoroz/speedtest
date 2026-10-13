#!/usr/bin/env bash
# Подгружает KEY=VALUE из .env кубика, не перезаписывая уже заданные переменные.
# Usage: source scripts/load_cube_env.sh <path-to-.env>
# Требует bash (косвенное раскрытие ${!key}).
if [ "$#" -ne 1 ]; then
	printf 'load_cube_env: usage: source %s <path-to-.env>\n' "${BASH_SOURCE[0]}" >&2
	return 2 2>/dev/null || exit 2
fi

_load_cube_env_file="$1"
if [ ! -f "$_load_cube_env_file" ]; then
	printf 'load_cube_env: нет %s — сначала соответствующий make *-init-env\n' \
		"$_load_cube_env_file" >&2
	unset _load_cube_env_file
	return 1 2>/dev/null || exit 1
fi

while IFS= read -r _load_cube_env_line || [ -n "$_load_cube_env_line" ]; do
	case "$_load_cube_env_line" in
		'' | \#*) continue ;;
	esac
	[[ "$_load_cube_env_line" == *=* ]] || continue
	_load_cube_env_key="${_load_cube_env_line%%=*}"
	_load_cube_env_value="${_load_cube_env_line#*=}"
	_load_cube_env_value="${_load_cube_env_value%%$'\r'}"
	[[ "$_load_cube_env_key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
	# Уже заданная в окружении переменная (например PORT от e2e) важнее .env.
	if [ -z "${!_load_cube_env_key+x}" ]; then
		export "${_load_cube_env_key}=${_load_cube_env_value}"
	fi
done <"$_load_cube_env_file"

unset _load_cube_env_file _load_cube_env_line _load_cube_env_key _load_cube_env_value
