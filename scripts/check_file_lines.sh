#!/usr/bin/env bash
set -euo pipefail

code_limit="$1"
test_limit="$2"
exceptions_file="$3"
script_dir="$(cd "$(dirname "$0")" && pwd)"
declare -A exceptions
failed=0

# Тестовый путь: сегмент tests/test/__tests__/e2e или имя *.test.*/ *.spec.*/
# test_*.py / *_test.py / *_test.rs / *_tests.rs.
is_test_file() {
    local path="$1"
    local base="${path##*/}"
    case "$base" in
        *.test.*|*.spec.*|test_*.py|*_test.py|*_test.rs|*_tests.rs) return 0 ;;
    esac
    local rest="$path" segment
    while [ -n "$rest" ]; do
        segment="${rest%%/*}"
        case "$segment" in
            tests|test|__tests__|e2e) return 0 ;;
        esac
        [ "$rest" = "$segment" ] && break
        rest="${rest#*/}"
    done
    return 1
}

limit_for() {
    if is_test_file "$1"; then
        printf '%s' "$test_limit"
    else
        printf '%s' "$code_limit"
    fi
}

while IFS=' ' read -r path exception_limit; do
    [ -z "$path" ] && continue
    [[ "$path" == \#* ]] && continue
    file_limit="$(limit_for "$path")"
    if [ -z "$exception_limit" ] || ! [[ "$exception_limit" =~ ^[0-9]+$ ]] || (( exception_limit >= file_limit )); then
        printf 'check-file-lines: исключение %s должно быть меньше общего лимита %s.\n' "$path" "$file_limit" >&2
        exit 1
    fi
    exceptions["$path"]="$exception_limit"
done < "$exceptions_file"

while IFS= read -r -d '' file; do
    file_limit="${exceptions[$file]:-$(limit_for "$file")}"
    lines="$(wc -l < "$file")"
    if (( lines > file_limit )); then
        printf 'check-file-lines: %s содержит %s строк, лимит %s.\n' "$file" "$lines" "$file_limit" >&2
        failed=1
    fi
done < <(bash "$script_dir/git_files.sh" py rs js jsx ts tsx sh)

exit "$failed"
