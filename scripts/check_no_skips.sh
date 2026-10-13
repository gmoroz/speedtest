#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
# Тестовые skip/only/ignore; не-тестовые .skip(n)/.only( и runIf не ловим.
skip_pattern='pytest\.mark\.(skip|skipif|xfail)\b|pytest\.(skip|xfail|importorskip)\(|unittest\.(skip|skipIf|skipUnless)\(|#\[ignore\b|\b(describe|it|test|suite|context)\.(skip|skipIf|only|todo|fails|fail|fixme)\(|\bxit\(|\bxdescribe\('
# Подавление coverage в исходниках.
cover_pattern='v8 ignore|istanbul ignore|c8 ignore|pragma:[[:space:]]*no cover'
failed=0

while IFS= read -r -d '' file; do
    if matches="$(grep -nE "$skip_pattern" "$file" || true)"; then
        [ -z "$matches" ] || {
            printf 'check-no-skips: пропущенный тест в %s\n%s\n' "$file" "$matches" >&2
            failed=1
        }
    fi
    if matches="$(grep -nE "$cover_pattern" "$file" || true)"; then
        [ -z "$matches" ] || {
            printf 'check-no-skips: подавление coverage в %s\n%s\n' "$file" "$matches" >&2
            failed=1
        }
    fi
done < <(bash "$script_dir/git_files.sh" py rs js jsx ts tsx)

exit "$failed"
