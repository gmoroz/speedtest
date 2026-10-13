#!/usr/bin/env bash
set -euo pipefail

# Выбор целей по изменённым путям. CHANGED_SCOPE=cached — только индекс (pre-commit);
# иначе — коммиты от upstream/origin/HEAD, staged, unstaged и untracked (full-check).
# RUN_TESTS=0 пропускает test-цели (pre-commit). CHECK_LABEL — префикс сообщений.
changed_scope="${CHANGED_SCOPE:-}"
run_tests="${RUN_TESTS:-1}"
check_label="${CHECK_LABEL:-full-check}"

force_full="$1"
ci="$2"
core_code_paths="$3"
project_format_targets="$4"
project_lint_targets="$5"
project_test_targets="$6"
shift 6

declare -a code_check_ids=()
declare -a code_check_paths=()
declare -a code_check_format_targets=()
declare -a code_check_lint_targets=()
declare -a code_check_test_targets=()

while [ "$#" -gt 0 ]; do
    if [ "$1" != --code-check ] || [ "$#" -lt 6 ]; then
        printf '%s: некорректная регистрация проверки кода.\n' "$check_label" >&2
        exit 2
    fi
    code_check_ids+=("$2")
    code_check_paths+=("$3")
    code_check_format_targets+=("$4")
    code_check_lint_targets+=("$5")
    code_check_test_targets+=("$6")
    shift 6
done

changed_files_file="$(mktemp)"
trap 'rm -f "$changed_files_file"' EXIT
full_run=0
full_reason=""

if [ -n "$force_full" ]; then
    full_run=1
    full_reason="FULL задан"
elif [ "$ci" = true ]; then
    full_run=1
    full_reason="CI=true"
elif [ "$changed_scope" = cached ]; then
    if ! git diff --name-only -z --cached > "$changed_files_file"; then
        full_run=1
        full_reason="не удалось вычислить изменённые файлы"
    fi
else
    if git rev-parse --verify --quiet '@{upstream}' >/dev/null; then
        comparison_base='@{upstream}'
    elif git rev-parse --verify --quiet origin/HEAD >/dev/null; then
        comparison_base='origin/HEAD'
    else
        full_run=1
        full_reason="не найдены @{upstream} и origin/HEAD"
    fi

    if [ "$full_run" -eq 0 ]; then
        if ! git diff --name-only -z "$comparison_base...HEAD" > "$changed_files_file" \
            || ! git diff --name-only -z >> "$changed_files_file" \
            || ! git diff --name-only -z --cached >> "$changed_files_file" \
            || ! git ls-files --others --exclude-standard -z >> "$changed_files_file"; then
            full_run=1
            full_reason="не удалось вычислить изменённые файлы"
        fi
    fi
fi

declare -a changed_files=()
if [ "$full_run" -eq 0 ]; then
    while IFS= read -r -d '' changed_file; do
        changed_files+=("$changed_file")
    done < "$changed_files_file"
fi

markdown_only=0
if [ "$full_run" -eq 0 ] && [ "${#changed_files[@]}" -gt 0 ]; then
    markdown_only=1
    for changed_file in "${changed_files[@]}"; do
        case "$changed_file" in
            *.md) ;;
            *) markdown_only=0; break ;;
        esac
    done
fi

path_is_changed() {
    local paths="$1"
    local code_path
    local changed_file
    for code_path in $paths; do
        for changed_file in "${changed_files[@]}"; do
            case "$changed_file" in
                "$code_path"|"$code_path"/*) return 0 ;;
            esac
        done
    done
    return 1
}

run_targets() {
    [ "$#" -eq 0 ] && return
    make --no-print-directory FULL_CHECK_FORMATTED=1 "$@"
}

declare -a selected_format_targets=()
declare -a selected_lint_targets=()
declare -a selected_test_targets=()
declare -a selected_project_lint_targets=()
declare -a skipped_targets=()
declare -a targets=()

for index in "${!code_check_ids[@]}"; do
    if [ "$full_run" -eq 1 ] \
        || path_is_changed "$core_code_paths" \
        || path_is_changed "${code_check_paths[$index]}"; then
        read -r -a targets <<< "${code_check_format_targets[$index]}"
        selected_format_targets+=("${targets[@]}")
        read -r -a targets <<< "${code_check_lint_targets[$index]}"
        selected_lint_targets+=("${targets[@]}")
        if [ "$run_tests" != 0 ]; then
            read -r -a targets <<< "${code_check_test_targets[$index]}"
            selected_test_targets+=("${targets[@]}")
        fi
    else
        if [ "$run_tests" != 0 ]; then
            read -r -a targets <<< "${code_check_format_targets[$index]} ${code_check_lint_targets[$index]} ${code_check_test_targets[$index]}"
        else
            read -r -a targets <<< "${code_check_format_targets[$index]} ${code_check_lint_targets[$index]}"
        fi
        skipped_targets+=("${targets[@]}")
    fi
done

if [ "$full_run" -eq 1 ]; then
    printf '%s: полный прогон (%s).\n' "$check_label" "$full_reason"
elif [ "${#skipped_targets[@]}" -gt 0 ]; then
    printf '%s: пропущены проверки кода: %s (нет изменений в путях кубиков и общей инфраструктуре).\n' \
        "$check_label" "${skipped_targets[*]}"
fi

read -r -a targets <<< "$project_format_targets"
run_targets "${targets[@]}" "${selected_format_targets[@]}"
read -r -a targets <<< "$project_lint_targets"
jscpd_skipped=0
for target in "${targets[@]}"; do
    if [ "$markdown_only" -eq 1 ] && [ "$target" = check-jscpd ]; then
        jscpd_skipped=1
        continue
    fi
    selected_project_lint_targets+=("$target")
done
if [ "$jscpd_skipped" -eq 1 ]; then
    printf '%s: пропущена проверка check-jscpd: изменены только markdown-файлы.\n' "$check_label"
fi
run_targets "${selected_project_lint_targets[@]}" "${selected_lint_targets[@]}"
if [ "$run_tests" != 0 ]; then
    read -r -a targets <<< "$project_test_targets"
    run_targets "${targets[@]}" "${selected_test_targets[@]}"
fi
