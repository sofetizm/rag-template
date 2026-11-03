"""Builds data/demo/fastapi-ru from the FastAPI repository (MIT license).

git clone --depth 1 https://github.com/fastapi/fastapi.git /tmp/fastapi
python scripts/prepare_demo.py /tmp/fastapi
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
from pathlib import Path

SKIP = {"_llm-test.md", "translation-banner.md", "help-fastapi.md", "benchmarks.md"}
ADMONITIONS = {
    "note": "Примечание",
    "tip": "Подсказка",
    "warning": "Внимание",
    "danger": "Опасность",
    "info": "Информация",
    "check": "Проверка",
    "details": "Подробнее",
    "tab": "Вариант",
}
INCLUDE = re.compile(r"\{\*\s*(\S+)(.*?)\*\}")
RAW_INCLUDE = re.compile(r"\{!>?\s*(\S+?)\s*!\}")
ADMONITION = re.compile(r"^/{3,4}\s*(\w+)\s*(?:\|\s*(.+))?$")


def parse_ranges(spec: str) -> list[tuple[int, int]]:
    ranges = []
    for part in spec.split(","):
        a, _, b = part.partition(":")
        ranges.append((int(a), int(b or a)))
    return ranges


def resolve(ref: str, doc_path: Path, repo: Path) -> Path | None:
    name = ref.split("docs_src/", 1)[-1]
    target = repo / "docs_src" / name
    return target if target.exists() else None


def raw_include(match: re.Match, doc_path: Path, repo: Path) -> str:
    target = resolve(match.group(1), doc_path, repo)
    return target.read_text(encoding="utf-8").rstrip() if target else ""


def include(match: re.Match, doc_path: Path, repo: Path) -> str:
    target = resolve(match.group(1), doc_path, repo)
    if target is None:
        return ""
    lines = target.read_text(encoding="utf-8").rstrip().splitlines()
    ln = re.search(r"ln\[([^\]]+)\]", match.group(2))
    if ln:
        selected = []
        for a, b in parse_ranges(ln.group(1)):
            if selected:
                selected.append("# ...")
            selected.extend(lines[a - 1 : b])
        lines = selected
    lang = {".py": "python", ".toml": "toml", ".json": "json", ".sh": "bash"}.get(target.suffix, "")
    return f"```{lang}\n" + "\n".join(lines) + "\n```"


def clean(text: str, doc_path: Path, repo: Path) -> str:
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        admonition = ADMONITION.match(stripped)
        if admonition:
            kind, title = admonition.groups()
            out.append(f"**{(title or ADMONITIONS.get(kind, kind)).strip()}:**")
            continue
        if re.fullmatch(r"/{3,4}", stripped):
            out.append("")
            continue
        out.append(line)
    text = "\n".join(out)
    text = INCLUDE.sub(lambda m: include(m, doc_path, repo), text)
    text = RAW_INCLUDE.sub(lambda m: raw_include(m, doc_path, repo), text)
    text = re.sub(r"^([ \t]*```)[ \t]*(\w*)[^\n]*$", lambda m: m.group(1) + m.group(2).lower(), text, flags=re.M)
    text = re.sub(r"\{\s*\.[\w\-]+[^}]*\}", "", text)
    text = re.sub(r'<abbr title="([^"]*)">(.*?)</abbr>', r"\2 (\1)", text, flags=re.S)
    text = re.sub(r"<dfn[^>]*>(.*?)</dfn>", r"\1", text, flags=re.S)
    text = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.S)
    text = re.sub(r"<img[^>]*>", "", text)
    text = re.sub(r"</?(font|span|div|b|u|strong|code|kbd|br|td|tr|table|th|thead|tbody|p|em|i|small)[^>]*>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/demo/fastapi-ru"))
    args = parser.parse_args()
    src = args.repo / "docs" / "ru" / "docs"
    if args.out.exists():
        shutil.rmtree(args.out)
    count = 0
    for path in sorted(src.rglob("*.md")):
        rel = path.relative_to(src)
        if rel.name in SKIP:
            continue
        target = args.out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(clean(path.read_text(encoding="utf-8"), path, args.repo), encoding="utf-8")
        count += 1
    commit = subprocess.run(
        ["git", "-C", str(args.repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    (args.out / "NOTICE").write_text(
        "Русская документация FastAPI, https://github.com/fastapi/fastapi (docs/ru/docs), "
        f"коммит {commit}.\nCopyright (c) 2018 Sebastián Ramírez. Лицензия MIT (файл LICENSE).\n"
        "Примеры кода из docs_src вставлены на место директив {* ... *}.\n",
        encoding="utf-8",
    )
    shutil.copy(args.repo / "LICENSE", args.out / "LICENSE")
    print(f"{count} pages -> {args.out}")


if __name__ == "__main__":
    main()
