#!/usr/bin/env bash
set -euo pipefail

version="$1"
script_dir="$(cd "$(dirname "$0")" && pwd)"
jscpd_bin="$script_dir/node_modules/.bin/jscpd"
report_dir="$(mktemp -d)"
trap 'rm -rf "$report_dir"' EXIT

if [ ! -x "$jscpd_bin" ]; then
    printf 'check-jscpd: нет %s; выполни make install\n' "$jscpd_bin" >&2
    exit 1
fi
installed="$(node -p "require('$script_dir/node_modules/jscpd/package.json').version")"
if [ "$installed" != "$version" ]; then
    printf 'check-jscpd: установлена jscpd %s, ожидается %s\n' "$installed" "$version" >&2
    exit 1
fi

# Каталоги кубиков из answers: строки "<layer> <dir>". Экземпляры одного кубика
# рождаются из одного шаблона, поэтому одинаковый файл в них — не копипаст.
instances=""
for answers in .copier-answers-*.yml; do
    layer="$(sed -n 's/^layer:[[:space:]]*//p' "$answers" | tr -d "\"'")"
    dir="$(sed -n "s/^${layer//-/_}_dir:[[:space:]]*//p" "$answers" | tr -d "\"'")"
    if [ -n "$dir" ]; then
        instances+="$layer $dir"$'\n'
    fi
done

# jscpd по умолчанию уважает .gitignore; .git в ignore — он обычно не в .gitignore.
status=0
"$jscpd_bin" --min-lines 10 --min-tokens 50 --threshold 0 --fail-on-empty \
    --format "bash,python,typescript,javascript,jsx,tsx,rust" --ignore "**/.git/**" \
    --reporters json --output "$report_dir" . > "$report_dir/jscpd.log" 2>&1 || status=$?
if [ ! -f "$report_dir/jscpd-report.json" ]; then
    cat "$report_dir/jscpd.log" >&2
    exit "$(( status == 0 ? 1 : status ))"
fi

node -e '
const fs = require("node:fs");
const [reportPath, instancesText] = process.argv.slice(1);
const dirs = instancesText.split("\n").filter(Boolean).map((line) => line.split(" "));
const locate = (file) => {
    const found = dirs.find(([, dir]) => file.startsWith(`${dir}/`));
    if (found === undefined) {
        return undefined;
    }
    // Имя файла и глубина, а не полный путь: у python-cli пакет src/<pkg_name>/ свой в каждом экземпляре.
    const segments = file.slice(found[1].length + 1).split("/");
    return { layer: found[0], dir: found[1], shape: `${segments.length}:${segments.at(-1)}` };
};
const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
if (report.statistics.total.sources === 0) {
    console.error("check-jscpd: нет исходников для проверки");
    process.exit(1);
}
const clones = report.duplicates.filter(({ firstFile, secondFile }) => {
    const first = locate(firstFile.name);
    const second = locate(secondFile.name);
    const sameTemplateFile = first !== undefined && second !== undefined && first.dir !== second.dir
        && first.layer === second.layer && first.shape === second.shape;
    return !sameTemplateFile;
});
for (const { firstFile, secondFile } of clones) {
    console.error(`check-jscpd: клон ${firstFile.name}:${firstFile.start}-${firstFile.end} = ${secondFile.name}:${secondFile.start}-${secondFile.end}`);
}
process.exit(clones.length === 0 ? 0 : 1);
' "$report_dir/jscpd-report.json" "$instances"
printf 'check-jscpd: OK\n'
