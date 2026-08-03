#!/usr/bin/env python3
"""Content-preserving HTML UTTR → GitHub-flavored Markdown for Giscus.

Strips layout chrome (style, split-pane divs) while keeping prose, lists,
headings, code, blockquotes, and mermaid. Does not invent or summarize content.
"""
from __future__ import annotations

import html as html_lib
import re
import sys
from html.parser import HTMLParser
from typing import List, Optional, Tuple

POLLUTION = re.compile(
    r"<!DOCTYPE|<html\b|<style\b|uttr-grid|policy-pane|mechanism-pane|ragnarox-uttr",
    re.I,
)


class _ToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self._skip_depth = 0  # inside style/script
        self._list_depth = 0
        self._in_pre = False
        self._pre_buf: List[str] = []
        self._in_code_inline = False
        self._blockquote = 0
        self._mermaid = False
        self._pending_li = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if self._skip_depth:
            if tag in ("style", "script"):
                self._skip_depth += 1
            return
        ad = {k: (v or "") for k, v in attrs}
        cls = ad.get("class", "")

        if tag in ("style", "script"):
            self._skip_depth = 1
            return
        if tag in ("div", "span", "section", "header", "footer", "main", "article"):
            if "mermaid" in cls.split():
                self._mermaid = True
                self.parts.append("\n\n```mermaid\n")
            # layout wrappers: no output
            return
        if tag == "br":
            self.parts.append("\n")
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.parts.append("\n\n" + ("#" * level) + " ")
            return
        if tag == "p":
            self.parts.append("\n\n")
            return
        if tag == "blockquote":
            self._blockquote += 1
            self.parts.append("\n\n")
            return
        if tag in ("ul", "ol"):
            self._list_depth += 1
            self.parts.append("\n")
            return
        if tag == "li":
            indent = "  " * max(0, self._list_depth - 1)
            self.parts.append(f"\n{indent}- ")
            self._pending_li = True
            return
        if tag == "pre":
            self._in_pre = True
            self._pre_buf = []
            return
        if tag == "code":
            if self._in_pre:
                return
            self._in_code_inline = True
            self.parts.append("`")
            return
        if tag in ("strong", "b"):
            self.parts.append("**")
            return
        if tag in ("em", "i"):
            self.parts.append("*")
            return
        if tag == "hr":
            self.parts.append("\n\n---\n\n")
            return
        if tag == "details":
            self.parts.append("\n\n")
            return
        if tag == "summary":
            self.parts.append("\n\n**")
            return
        # ignore other tags (a without special handling keeps text)

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            if tag in ("style", "script"):
                self._skip_depth -= 1
            return
        if tag in ("div", "span", "section", "header", "footer", "main", "article"):
            if self._mermaid and tag == "div":
                self.parts.append("\n```\n\n")
                self._mermaid = False
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self.parts.append("\n")
            return
        if tag == "blockquote":
            self._blockquote = max(0, self._blockquote - 1)
            self.parts.append("\n")
            return
        if tag in ("ul", "ol"):
            self._list_depth = max(0, self._list_depth - 1)
            self.parts.append("\n")
            return
        if tag == "li":
            self._pending_li = False
            return
        if tag == "pre":
            code = "".join(self._pre_buf).strip("\n")
            # decode residual entities if any
            code = html_lib.unescape(code)
            lang = "cpp" if (
                "#include" in code or "std::" in code or "bool " in code[:80]
            ) else ""
            fence = f"```{lang}\n{code}\n```"
            self.parts.append(f"\n\n{fence}\n\n")
            self._in_pre = False
            self._pre_buf = []
            return
        if tag == "code":
            if self._in_pre:
                return
            self._in_code_inline = False
            self.parts.append("`")
            return
        if tag in ("strong", "b"):
            self.parts.append("**")
            return
        if tag in ("em", "i"):
            self.parts.append("*")
            return
        if tag == "summary":
            self.parts.append("**\n\n")
            return

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_pre:
            self._pre_buf.append(data)
            return
        text = data
        if self._blockquote and text.strip():
            # prefix lines for blockquote
            lines = text.split("\n")
            text = "\n".join(
                ("> " + ln if ln.strip() else ">") for ln in lines
            )
        if self._mermaid:
            self.parts.append(text)
            return
        # collapse pure whitespace runs outside pre (keep single spaces)
        if not text.strip():
            if text and not self.parts:
                return
            if self.parts and not self.parts[-1].endswith((" ", "\n", "`", "*")):
                self.parts.append(" ")
            return
        self.parts.append(text)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(html_lib.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.handle_data(html_lib.unescape(f"&#{name};"))


def extract_leading_markdown(body: str) -> Tuple[str, str]:
    """Split optional pure-MD header from first HTML tag / details block."""
    # If body starts with MD then <details> or <div or <style
    m = re.search(r"(?is)(<details\b|<div\b|<style\b|<!DOCTYPE)", body)
    if not m:
        if POLLUTION.search(body):
            return "", body
        return body, ""
    return body[: m.start()].rstrip(), body[m.start() :]


def html_fragment_to_md(fragment: str) -> str:
    # Wrap fragment so parser is happy
    parser = _ToMarkdown()
    parser.feed(fragment)
    parser.close()
    md = "".join(parser.parts)
    # cleanup
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = html_lib.unescape(md)
    # drop collapsible chrome lines that only advertise HTML
    md = re.sub(
        r"(?im)^\*\*Open full UTTR split-pane record \(HTML\)\*\*\s*\n*",
        "",
        md,
    )
    md = re.sub(r"(?im)^Open full UTTR split-pane record \(HTML\)\s*\n*", "", md)
    return md.strip()


def convert_uttr_body(body: str) -> str:
    head, html_part = extract_leading_markdown(body)
    if not html_part:
        # whole body may still be mixed; try full convert if pollution
        if POLLUTION.search(body):
            return html_fragment_to_md(body)
        return body.strip()
    converted = html_fragment_to_md(html_part)
    if head:
        out = head.rstrip() + "\n\n" + converted
    else:
        out = converted
    # Ensure format line prefers Markdown
    out = re.sub(
        r"(?im)(\*\*Format:\*\*[^\n]*split-pane[^\n]*)",
        "**Format:** NASA/SP-2016-6105 Rev2 UTTR (Markdown for Giscus)",
        out,
    )
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    return out


def is_polluted(body: str) -> bool:
    return bool(POLLUTION.search(body or ""))


def gate_ok(original: str, converted: str) -> Tuple[bool, str]:
    if is_polluted(converted):
        return False, "residual pollution markers in converted body"
    # text length from original without tags
    plain_orig = re.sub(r"(?is)<style.*?</style>", "", original)
    plain_orig = re.sub(r"<[^>]+>", " ", plain_orig)
    plain_orig = re.sub(r"\s+", " ", plain_orig).strip()
    plain_new = re.sub(r"\s+", " ", converted).strip()
    if len(plain_orig) > 200 and len(plain_new) < 0.4 * len(plain_orig):
        return False, f"length ratio too low: {len(plain_new)}/{len(plain_orig)}"
    for token in ("UTTR", "RAGnaroX"):
        if token in original and token not in converted:
            # case-insensitive fallback
            if token.lower() not in converted.lower():
                return False, f"missing token {token}"
    if "2604.03291" in original and "2604.03291" not in converted:
        return False, "missing arXiv id"
    return True, "ok"


def main() -> int:
    data = sys.stdin.read()
    out = convert_uttr_body(data)
    ok, msg = gate_ok(data, out)
    if not ok:
        print(f"GATE_FAIL: {msg}", file=sys.stderr)
        sys.stdout.write(out)
        return 2
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
