#!/usr/bin/env python3
"""Generate the black terminal-window panels used by the profile README.

Each panel is a self-contained SVG: black body, macOS-style title bar, and
monospace text laid out as terminal output. Text is emitted one <text> element
per line with xml:space="preserve", so column alignment survives whichever
monospace face the viewer's machine resolves.

Usage: python3 .github/scripts/build_terminal_svgs.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "assets"

# ---------------------------------------------------------------- palette ---
BG = "#000000"
BAR = "#0d1117"
BORDER = "#21262d"
TITLE = "#6e7681"

GREEN = "#3fb950"   # prompt
CYAN = "#39c5cf"    # user/host, keys
BLUE = "#58a6ff"    # paths, names
TEXT = "#c9d1d9"    # normal output
DIM = "#8b949e"     # secondary output
ORANGE = "#ff7b29"  # accents
PURPLE = "#bc8cff"  # languages

FS = 13             # font size
CW = FS * 0.6       # monospace advance width
LH = 21             # line height
PAD_X = 22
BAR_H = 34
PAD_TOP = 16
PAD_BOTTOM = 18
WIDTH = 840
MAX_CHARS = int((WIDTH - 2 * PAD_X) / CW)

FONT = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'DejaVu Sans Mono', monospace")

ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def esc(s):
    for k, v in ESCAPES.items():
        s = s.replace(k, v)
    return s


def seg(text, color=TEXT):
    """One colored run of text within a line."""
    return (text, color)


def prompt(cmd):
    """A `$ command` line."""
    return [seg("$ ", GREEN), seg(cmd, TEXT)]


def render(name, title, lines, center_lines=()):
    """Write one panel.

    `lines` holds one entry per rendered row: a list of segments, None for a
    blank row, or a ``Raw`` block of literal SVG occupying a fixed height.
    Indices listed in `center_lines` are centered instead of left-aligned.
    """
    for i, line in enumerate(lines):
        if line is None or isinstance(line, Raw):
            continue
        width = sum(len(t) for t, _ in line)
        if width > MAX_CHARS:
            raise SystemExit(
                f"{name}: line {i} is {width} chars, max is {MAX_CHARS}\n"
                f"  {''.join(t for t, _ in line)}"
            )

    body = sum(line.height if isinstance(line, Raw) else LH for line in lines)
    height = BAR_H + PAD_TOP + body + PAD_BOTTOM
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'font-family="{FONT}" font-size="{FS}">',
        "<style>"
        ".blink{animation:b 1.06s steps(1) infinite}"
        "@keyframes b{50%{opacity:0}}"
        "</style>",
        f'<rect width="{WIDTH}" height="{height}" rx="10" fill="{BG}" '
        f'stroke="{BORDER}"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{WIDTH - 20}a10 10 0 0 1 10 10'
        f'v{BAR_H - 10}H0z" fill="{BAR}"/>',
        f'<line x1="0" y1="{BAR_H}" x2="{WIDTH}" y2="{BAR_H}" '
        f'stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{20 + i * 19}" cy="{BAR_H / 2}" r="5.5" '
                   f'fill="{color}"/>')
    out.append(f'<text x="{WIDTH / 2}" y="{BAR_H / 2 + 4}" fill="{TITLE}" '
               f'font-size="11.5" text-anchor="middle">{esc(title)}</text>')

    y = BAR_H + PAD_TOP
    for i, line in enumerate(lines):
        if isinstance(line, Raw):
            out.append(f'<g transform="translate(0 {y})">{line.svg}</g>')
            y += line.height
            continue
        if line:
            width = sum(len(t) for t, _ in line)
            x = (WIDTH - width * CW) / 2 if i in center_lines else PAD_X
            spans = "".join(
                f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in line
            )
            out.append(f'<text x="{x:.1f}" y="{y + FS}" '
                       f'xml:space="preserve">{spans}</text>')
        y += LH
    out.append("</svg>")

    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}.svg").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  assets/{name}.svg  ({WIDTH}x{height})")


# A 5x7 bitmap face for the wordmark. Drawing the name as rects rather than
# box-drawing characters keeps it identical everywhere — figlet-style ASCII art
# relies on glyph metrics that differ per font and tears apart at the seams.
GLYPHS = {
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "M": ("10001", "11011", "10101", "10001", "10001", "10001", "10001"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    " ": ("00000",) * 7,
}

UNIT = 7        # pixel size of one bitmap cell
GLYPH_GAP = 1   # cells between letters


class Raw:
    """Literal SVG occupying `height` pixels in a panel's line flow."""

    def __init__(self, svg, height):
        self.svg = svg
        self.height = height


def wordmark(word, pad=10):
    cells = (len(word) * (5 + GLYPH_GAP) - GLYPH_GAP)
    w, h = cells * UNIT, 7 * UNIT
    x0 = (WIDTH - w) / 2
    rects = []
    for i, ch in enumerate(word):
        gx = x0 + i * (5 + GLYPH_GAP) * UNIT
        for row, bits in enumerate(GLYPHS[ch]):
            run = 0
            for col in range(6):  # one past the end flushes the final run
                on = col < 5 and bits[col] == "1"
                if on:
                    run += 1
                elif run:
                    rects.append(
                        f'<rect x="{gx + (col - run) * UNIT:.0f}" '
                        f'y="{pad + row * UNIT}" width="{run * UNIT}" '
                        f'height="{UNIT}" fill="url(#wm)"/>'
                    )
                    run = 0
    grad = (f'<defs><linearGradient id="wm" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{CYAN}"/>'
            f'<stop offset="1" stop-color="{BLUE}"/></linearGradient></defs>')
    return Raw(grad + "".join(rects), h + pad * 2)


def build_header():
    lines = [
        [seg("$ ", GREEN), seg("ssh ", TEXT), seg("himanshu@github.com", CYAN)],
        [seg("Connection established.", DIM)],
        wordmark("HIMANSHU KUMAR"),
        [seg("AI Engineer @ Britcore.ai   ·   Founder, OpenAgentHQ   ·   "
             "Open Source", TEXT)],
        [seg("Building agentic systems, LLM infrastructure & developer "
             "tools.", DIM)],
    ]
    render("header", "himanshu@github: ~", lines, {3, 4})


def kv(key, value, key_color=CYAN, value_color=TEXT, width=12):
    return [seg("  " + key.ljust(width), key_color), seg(value, value_color)]


def build_whoami():
    render("whoami", "whoami — bash", [
        prompt("whoami --verbose"),
        None,
        kv("role", "AI Engineer @ Britcore.ai"),
        kv("oss", "Founder, OpenAgentHQ"),
        kv("focus", "agentic systems · LLM infrastructure · RAG · devtools"),
        kv("ships", "eval frameworks, model runtimes, CLIs published to PyPI"),
        kv("portfolio", "himanshu231204.vercel.app", value_color=BLUE),
        kv("email", "himanshu231204@gmail.com", value_color=BLUE),
    ])


def build_stack():
    render("stack", "cat stack.txt — bash", [
        prompt("cat stack.txt"),
        None,
        kv("languages", "Python · TypeScript · SQL", value_color=PURPLE),
        kv("ai/ml", "PyTorch · LangChain · LangGraph · Hugging Face"),
        kv("", "OpenAI · Anthropic · Ollama"),
        kv("infra", "FastAPI · Docker · Redis · ChromaDB · GitHub Actions"),
        kv("tooling", "Git · Linux · pytest · MCP"),
    ])


PROJECTS = [
    ("openagent-eval", "Python", "RAG + agent evaluation · 18+ metrics · CLI & SDK"),
    ("modeldock", "Python", "local LLM manager · pluggable runtime adapters"),
    ("run-git", "Python", "PyPI CLI · git workflows in a single command"),
    ("mcp-web-search", "Python", "production MCP server · search + page extraction"),
    ("ai-comment-copilot", "Python", "chrome extension · LangGraph multi-agent flows"),
    ("ai-news-intelligence", "Python", "agent · monitors high-signal AI research"),
]


def build_projects():
    lines = [prompt("ls -la ~/projects"), None]
    for name, lang, desc in PROJECTS:
        lines.append([
            seg("drwxr-xr-x  ", DIM),
            seg(name.ljust(22), BLUE),
            seg(lang.ljust(12), PURPLE),
            seg(desc, TEXT),
        ])
    render("projects", "ls -la ~/projects — bash", lines)


OSS = [
    ("langchain-ai/openwiki", "connector features, error handling, workflow preservation"),
    ("OpenAgentHQ/openagent-eval", "13+ merged PRs · review workflows, tests, releases"),
    ("OpenAgentHQ/modeldock", "LM Studio runtime adapter, CI/CD fixes"),
    ("himanshu231204/avenx-js", "compiler documentation"),
]


def build_oss():
    lines = [prompt("git log --author=himanshu231204 --oneline"), None]
    for repo, work in OSS:
        lines.append([
            seg("*  ", ORANGE),
            seg(repo.ljust(29), BLUE),
            seg(work, TEXT),
        ])
    render("oss", "git log — bash", lines)


WRITING = [
    ("system-design-fundamentals", "16 runnable demos + a RAG API across 6 scaling stages"),
    ("prompt-engineering-mastery", "7 modules · reasoning, RAG, security, evaluation"),
    ("PyTorch-Mastery", "tensors and autograd through LLM fine-tuning"),
    ("ml-mastery", "algorithms, notebooks, and reference guides"),
    ("dl-mastery", "math-first deep learning, derivations to code"),
]


def build_writing():
    lines = [
        prompt("man himanshu"),
        None,
        [seg("  Long-form engineering references, written for practitioners.",
             DIM)],
        None,
    ]
    for repo, desc in WRITING:
        lines.append([
            seg("  -rw-r--r--  ", DIM),
            seg(repo.ljust(28), BLUE),
            seg(desc, TEXT),
        ])
    render("writing", "man himanshu — bash", lines)


def build_status():
    render("status", "himanshu@github: ~", [
        [seg("$ ", GREEN), seg("echo ", TEXT), seg("$STATUS", CYAN)],
        None,
        [seg("  Open to collaboration on agentic systems, LLM "
             "infrastructure, and devtools.", TEXT)],
        None,
        [seg("himanshu@github", CYAN), seg(":", TEXT), seg("~", BLUE),
         seg("$ ", TEXT), ("█", GREEN)],
    ])
    # mark the trailing cursor as blinking
    path = OUT / "status.svg"
    svg = path.read_text(encoding="utf-8")
    svg = svg.replace(f'<tspan fill="{GREEN}">█</tspan>',
                      f'<tspan class="blink" fill="{GREEN}">█</tspan>')
    path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    print(f"building panels ({WIDTH}px wide, {MAX_CHARS} chars max)")
    build_header()
    build_whoami()
    build_stack()
    build_projects()
    build_oss()
    build_writing()
    build_status()
