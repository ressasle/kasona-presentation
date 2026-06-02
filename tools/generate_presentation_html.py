#!/usr/bin/env python3
"""
generate_presentation_html.py — Company Presentation → Rich HTML Dashboard

Converts a Markdown presentation + Supabase company_presentation row into a
premium HTML report with Kasona branding.
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

def load_env():
    env = {}
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def md_inline(text: str) -> str:
    """Convert inline Markdown (bold, italic) to HTML."""
    if not text: return ""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Newlines
    text = text.replace("\n", "<br>")
    return text

def md_to_html_body(md_text: str) -> str:
    """Convert a block of Markdown to HTML for embedding in a section."""
    if not md_text: return ""
    lines = md_text.splitlines()
    html_parts = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("### "):
            html_parts.append(f'<h3 class="section-h3">{stripped[4:]}</h3>')
            i += 1
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                item = lines[i].strip()[2:]
                list_items.append(f"<li>{md_inline(item)}</li>")
                i += 1
            html_parts.append(f'<ul class="md-list">{"".join(list_items)}</ul>')
            continue

        if stripped:
            html_parts.append(f'<p class="md-p">{md_inline(stripped)}</p>')

        i += 1

    return "\n".join(html_parts)

CSS = """
:root {
  --kasona-orange: #f36c21;
  --kasona-blue: #1e3a8a;
  --kasona-dark: #0f172a;
  --text: #1e293b;
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --border: #e2e8f0;
  --font: 'Inter', system-ui, sans-serif;
}

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  margin: 0;
  padding: 0;
}

.page-wrapper { max-width: 900px; margin: 40px auto; padding: 0 20px; }

.header {
  background: var(--kasona-dark);
  color: white;
  padding: 60px 0;
  text-align: center;
  border-bottom: 5px solid var(--kasona-orange);
}

.company-logo {
  max-width: 120px;
  margin-bottom: 20px;
}

.header h1 { margin: 0; font-size: 2.5rem; letter-spacing: -1px; }
.header p { opacity: 0.8; margin-top: 10px; font-size: 1.1rem; }

.card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  border: 1px solid var(--border);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--kasona-blue);
  margin-bottom: 20px;
  border-bottom: 2px solid var(--bg);
  padding-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.section-h3 { color: var(--kasona-dark); margin-top: 25px; }

.md-list { padding-left: 20px; }
.md-list li { margin-bottom: 10px; }

.footer {
  text-align: center;
  padding: 40px 0;
  color: #64748b;
  font-size: 0.9rem;
  border-top: 1px solid var(--border);
}

.badge {
  background: var(--kasona-orange);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
}

@media (max-width: 600px) {
  .header h1 { font-size: 1.8rem; }
}
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown_file")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    md_path = Path(args.markdown_file)
    if not md_path.exists():
        print(f"Error: {md_path} not found")
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    
    # Simple extraction of sections based on ##
    sections = {}
    current_title = "Intro"
    current_lines = []
    for line in md_text.splitlines():
        if line.startswith("## "):
            sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip().split(". ", 1)[-1]
            current_lines = []
        else:
            current_lines.append(line)
    sections[current_title] = "\n".join(current_lines).strip()

    ticker = args.ticker.upper()
    generated_date = datetime.now().strftime("%B %d, %Y")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ticker} | Institutional Presentation</title>
    <style>{CSS}</style>
</head>
<body>
    <header class="header">
        <div class="page-wrapper" style="margin:0 auto; padding:0;">
            <span class="badge">INSTITUTIONAL BRIEFING</span>
            <h1>{ticker} Strategic Analysis</h1>
            <p>Comprehensive Overview & Governance Audit</p>
        </div>
    </header>

    <div class="page-wrapper">
"""

    for title, content in sections.items():
        if not content: continue
        body_html = md_to_html_body(content)
        html_content += f"""
        <div class="card">
            <div class="card-title">{title}</div>
            {body_html}
        </div>
"""

    html_content += f"""
    </div>

    <footer class="footer">
        <p>&copy; {datetime.now().year} Kasona Production | <a href="https://kasona.ai">kasona.ai</a></p>
        <p>Generated on {generated_date} | Purely for institutional research purposes.</p>
    </footer>
</body>
</html>
"""

    output_path = Path(args.output_dir) / f"{ticker.replace('.', '_').lower()}_presentation.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"[OK] HTML Presentation generated: {output_path}")

if __name__ == "__main__":
    main()
