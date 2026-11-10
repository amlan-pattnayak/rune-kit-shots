#!/usr/bin/env python3
"""Reads rune-kit's source into api.json (public types, variants, builder methods with their doc
comments) and stories.json (gallery scene id -> the story function's source).

usage: extract.py <rune checkout> <out dir>
"""
import json
import re
import sys
from pathlib import Path

RUNE, OUT = Path(sys.argv[1]), Path(sys.argv[2])
KIT = RUNE / "crates/rune-kit/src"
GAL = RUNE / "examples/kit-gallery/src"


def clean_doc(lines):
    return " ".join(l.strip().removeprefix("///").strip() for l in lines).strip()


def parse(path):
    """Top-level pub structs/enums and the pub fns of their inherent impls."""
    types, order, loose = {}, [], {}
    cur_trait = None
    lines = path.read_text().splitlines()
    doc, cur_impl, cur_enum, i = [], None, None, 0
    in_tests = False
    while i < len(lines):
        l = lines[i]
        s = l.strip()
        if l.startswith("#[cfg(test)]"):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if nxt.startswith("mod ") and nxt.rstrip().endswith("{"):
                in_tests = True
            else:
                i += 1
                continue
        if in_tests:
            i += 1
            continue
        if s.startswith("///"):
            doc.append(s)
            i += 1
            continue
        if s.startswith("#["):
            i += 1
            continue
        m = re.match(r"pub (struct|enum|trait) (\w+)", l)
        if m:
            kind, name = m.groups()
            types[name] = {"kind": kind, "doc": clean_doc(doc), "variants": [], "methods": []}
            order.append(name)
            cur_enum = name if kind == "enum" else None
            cur_trait = name if kind == "trait" else None
            doc = []
            i += 1
            continue
        m = re.match(r"pub fn (\w+)", l)
        if m:
            sig, j = s, i
            while "{" not in sig and j + 1 < len(lines) and j - i < 8:
                j += 1
                sig += " " + lines[j].strip()
            sig = re.sub(r"\s*(where .*)?\{.*$", "", sig).removeprefix("pub ").strip()
            types[m.group(1)] = {"kind": "fn", "doc": clean_doc(doc), "variants": [], "methods": [], "sig": sig}
            order.append(m.group(1))
            doc = []
            i += 1
            continue
        if cur_enum and re.match(r"    [A-Z]\w*", l):
            v = re.match(r"    ([A-Z]\w*)", l).group(1)
            types[cur_enum]["variants"].append({"name": v, "doc": clean_doc(doc)})
            doc = []
            i += 1
            continue
        if l.startswith("}"):
            cur_enum, cur_impl, cur_trait = None, None, None
        m = re.match(r"impl(?:<[^>]*>)? (\w+)(?:<[^>]*>)? \{", l)
        if m:
            cur_impl = m.group(1)
        m = re.match(r"    pub (?:const )?fn (\w+)", l) or (cur_trait and re.match(r"    fn (\w+)", l))
        if m and (cur_impl or cur_trait):
            sig = s
            j = i
            while "{" not in sig and j + 1 < len(lines) and j - i < 8:
                j += 1
                sig += " " + lines[j].strip()
            sig = re.sub(r"\s*(where .*)?\{.*$", "", sig).removeprefix("pub ").strip()
            sig = re.sub(r"\bmut self\b", "self", sig)
            loose.setdefault(cur_trait or cur_impl, []).append({"name": m.group(1), "sig": sig, "doc": clean_doc(doc)})
        doc = []
        i += 1
    return [{"name": n, **types[n]} for n in order], loose


def module(rel):
    return rel.split("/")[0].removesuffix(".rs")


def fn_source(text, name):
    m = re.search(rf"^(?:pub(?:\(\w+\))? )?fn {name}\b", text, re.M)
    if not m:
        return None
    start = m.start()
    # include the doc comment above
    head = text[:start].splitlines()
    k = len(head)
    while k > 0 and head[k - 1].startswith("///"):
        k -= 1
    doc = "\n".join(head[k:])
    depth, i, seen = 0, text.index("{", start), False
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
            seen = True
        elif c == "}":
            depth -= 1
            if seen and depth == 0:
                break
        i += 1
    return (doc + "\n" if doc else "") + text[start:i + 1]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    api, parsed, methods = {}, {}, {}
    for p in sorted(KIT.rglob("*.rs")):
        if "test" in p.name:
            continue
        rel = str(p.relative_to(KIT))
        parsed[rel], loose = parse(p)
        for name, ms in loose.items():
            methods.setdefault(name, []).append((module(rel), ms))
    # An impl's methods go to the type of that name in the same module; if the name is defined
    # in one place only, impls elsewhere in the crate (Kit's, say) join it too.
    owners = {}
    for rel, ts in parsed.items():
        for t in ts:
            owners.setdefault(t["name"], []).append(module(rel))
    for rel, ts in parsed.items():
        for t in ts:
            if t["kind"] == "fn":
                continue
            unique = len(owners[t["name"]]) == 1
            t["methods"] = [m for mod, ms in methods.get(t["name"], []) if unique or mod == module(rel) for m in ms]
        ts = [t for t in ts if t["methods"] or t["variants"] or t["doc"] or t["kind"] == "fn"]
        if ts:
            api[rel] = ts
    (OUT / "api.json").write_text(json.dumps(api, indent=1))

    stories_rs = (GAL / "stories.rs").read_text()
    sources = {"stories.rs": stories_rs}
    for p in (GAL / "stories").glob("*.rs"):
        sources[p.stem] = p.read_text()
    stories = {}
    for sid, path in re.findall(r'^\s*"([\w-]+)" => ([\w:]+),', stories_rs, re.M):
        mod, _, fn = path.rpartition("::")
        cands = [sources[mod]] if mod else list(sources.values())
        src = next((s for s in (fn_source(t, fn) for t in cands) if s), None)
        stories[sid] = {"fn": fn, "src": src}
    (OUT / "stories.json").write_text(json.dumps(stories, indent=1))
    missing = [k for k, v in stories.items() if not v["src"]]
    print(len(api), "files;", sum(len(v) for v in api.values()), "types;", len(stories), "stories; missing source:", missing)


main()
