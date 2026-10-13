#!/usr/bin/env bash
set -euo pipefail

allowed=(
    AGENTS.md README.md Makefile .editorconfig .gitignore
    .githooks scripts mk .git
)
allowed+=("$@")
failed=0
declare -A seen=()

is_allowed() {
    local entry="$1"
    local allowed_entry
    for allowed_entry in "${allowed[@]}"; do
        [ "$entry" = "$allowed_entry" ] && return 0
    done
    return 1
}

# Каталог кубика может быть вложенным (apps/cli): тогда разрешён только он, а не весь apps.
has_nested_allowed() {
    local entry="$1"
    local allowed_entry
    for allowed_entry in "${allowed[@]}"; do
        [[ "$allowed_entry" == "$entry"/* ]] && return 0
    done
    return 1
}

is_nested_allowed() {
    local path="$1"
    local allowed_entry
    for allowed_entry in "${allowed[@]}"; do
        [[ "$allowed_entry" == */* && "$path" == "$allowed_entry"/* ]] && return 0
    done
    return 1
}

while IFS= read -r -d '' path; do
    entry="${path%%/*}"
    [ -n "${seen[$entry]:-}" ] && continue
    if is_allowed "$entry"; then
        seen["$entry"]=1
        continue
    fi
    if ! has_nested_allowed "$entry"; then
        seen["$entry"]=1
        printf 'check-root: неожиданный элемент в корне: %s\n' "$entry" >&2
        failed=1
        continue
    fi
    is_nested_allowed "$path" && continue
    printf 'check-root: неожиданный элемент в корне: %s\n' "$path" >&2
    failed=1
done < <(git ls-files -z --cached --others --exclude-standard)

exit "$failed"
