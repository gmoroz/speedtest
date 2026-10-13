#!/usr/bin/env bash
# Выделяет свободные TCP-порты в диапазоне 20000-32767 (ниже эфемерного Linux).
# Исключает порты, которые уже слушают, и значения из .env проекта.
# Usage: alloc_ports.sh <project_root> <count>
set -euo pipefail

readonly PORT_MIN=20000
readonly PORT_MAX=32767
readonly MAX_ATTEMPTS=1000

if [ "$#" -ne 2 ]; then
	printf 'alloc_ports: usage: %s <project_root> <count>\n' "$(basename "$0")" >&2
	exit 2
fi

project_root="$1"
count="$2"

if [ ! -d "$project_root" ]; then
	printf 'alloc_ports: нет каталога %s\n' "$project_root" >&2
	exit 1
fi

if ! [[ "$count" =~ ^[1-9][0-9]*$ ]]; then
	printf 'alloc_ports: count должен быть положительным целым, получено %s\n' "$count" >&2
	exit 2
fi

# Собирает уже зарезервированные порты из .env проекта (ключи и URL).
collect_reserved() {
	local root="$1"
	local file key value
	# -name '.env' и '.env.*', но не .env.example
	while IFS= read -r -d '' file; do
		case "$(basename "$file")" in
			.env.example) continue ;;
		esac
		# KEY=12345
		while IFS= read -r line || [ -n "$line" ]; do
			case "$line" in
				'' | \#*) continue ;;
			esac
			[[ "$line" == *=* ]] || continue
			key="${line%%=*}"
			value="${line#*=}"
			value="${value%%$'\r'}"
			if [[ "$value" =~ ^[0-9]+$ ]] &&
				[ "$value" -ge "$PORT_MIN" ] &&
				[ "$value" -le "$PORT_MAX" ]; then
				printf '%s\n' "$value"
			fi
			# URL вида host:PORT/ или host:PORT
			if [[ "$value" =~ :([0-9]{4,5})(/|$) ]]; then
				port="${BASH_REMATCH[1]}"
				if [ "$port" -ge "$PORT_MIN" ] && [ "$port" -le "$PORT_MAX" ]; then
					printf '%s\n' "$port"
				fi
			fi
		done <"$file"
	done < <(find "$root" \( -name .env -o -name '.env.*' \) -type f -print0 2>/dev/null)
}

# Порт уже слушают на машине.
port_listening() {
	local port="$1"
	ss -ltnH "sport = :$port" 2>/dev/null | grep -q .
}

declare -A reserved=()
while IFS= read -r port; do
	[ -n "$port" ] || continue
	reserved["$port"]=1
done < <(collect_reserved "$project_root" | sort -u)

allocated=()
attempts=0
while [ "${#allocated[@]}" -lt "$count" ]; do
	attempts=$((attempts + 1))
	if [ "$attempts" -gt "$MAX_ATTEMPTS" ]; then
		printf 'alloc_ports: не удалось выделить %s свободных портов за %s попыток\n' \
			"$count" "$MAX_ATTEMPTS" >&2
		exit 1
	fi
	candidate="$(shuf -i "${PORT_MIN}-${PORT_MAX}" -n 1)"
	if [ -n "${reserved[$candidate]+x}" ]; then
		continue
	fi
	already=0
	for taken in "${allocated[@]+"${allocated[@]}"}"; do
		if [ "$taken" = "$candidate" ]; then
			already=1
			break
		fi
	done
	if [ "$already" -eq 1 ]; then
		continue
	fi
	if port_listening "$candidate"; then
		reserved["$candidate"]=1
		continue
	fi
	allocated+=("$candidate")
	reserved["$candidate"]=1
done

printf '%s\n' "${allocated[@]}"
