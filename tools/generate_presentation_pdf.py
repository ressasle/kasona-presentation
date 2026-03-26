#!/usr/bin/env python3
"""
generate_presentation_pdf.py — Markdown → PDF for Company Presentations

Converts company structural analysis Markdown files into professional PDFs
with Kasona branding, company logos, and high-impact visual layouts.

Usage:
    python3 generate_presentation_pdf.py apple_presentation.md --ticker AAPL.US
"""

import argparse
import html
import os
import re
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

# ============================================================
# Configuration
# ============================================================

# Unicode font path (Windows)
UNICODE_FONT_DIR = "C:/Windows/Fonts/"
UNICODE_FONT_REGULAR = "consola.ttf"
UNICODE_FONT_BOLD = "consolab.ttf"
UNICODE_FONT_ITALIC = "consolai.ttf"
UNICODE_FONT_BOLD_ITALIC = "consolaz.ttf"

# Colors (RGB) — Monochromatic Professional (Blue/Gray/Black)
COLOR_PRIMARY_BLUE = (30, 58, 138)        # #1E3A8A — Primary Brand Blue
COLOR_KASONA_DARK = (15, 23, 42)          # #0f172a — Deep slate
COLOR_DARK = (15, 23, 42)                 # Black
COLOR_PRIMARY = (30, 58, 138)             # Blue for h2
COLOR_ACCENT = (51, 65, 85)               # #334155 — Slate-600
COLOR_TEXT = (15, 23, 42)                 # Black
COLOR_LIGHT_BG = (248, 250, 252)         # Very light gray/blue
COLOR_BORDER = (203, 213, 225)           # Light gray/blue border
COLOR_MUTED = (100, 116, 139)            # Muted gray
COLOR_WHITE = (255, 255, 255)
COLOR_TABLE_HEADER = (15, 23, 42)        # Deep black for tables
COLOR_COVER_BG = (15, 23, 42)           # Deep black cover
COLOR_KASONA_ORANGE = (243, 108, 33)     # #F36C21 — Kasona Orange

# Font Configuration
FONT = "Consolas"
SIZE_TITLE = 36
SIZE_HEADER = 28
SIZE_BODY = 18
SIZE_TABLE = 14
SIZE_MUTED = 10

def strip_emoji(text):
    """Remove emoji and other non-BMP characters."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U0000FE00-\U0000FE0F"
        "\U0000200D"
        "\U00002640-\U00002642"
        "\U00002600-\U000026FF"
        "\U0000231A-\U0000231B"
        "\U00002934-\U00002935"
        "\U000025AA-\U000025AB"
        "\U000025FB-\U000025FE"
        "\U000023E9-\U000023F3"
        "\U000023CF"
        "\U00002B05-\U00002B07"
        "\U00002B1B-\U00002B1C"
        "\U00002B50"
        "\U00002B55"
        "\U00003030"
        "\U0000303D"
        "\U00003297"
        "\U00003299"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def clean_text(text, strip_links=True):
    """Clean markdown formatting from text for plain display."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    if strip_links:
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = html.unescape(text)
    text = strip_emoji(text)
    return text.strip()

def download_company_logo(ticker, output_dir):
    """Download company logo from EODHD."""
    parts = ticker.split(".")
    if len(parts) != 2: return None
    symbol, exchange = parts[0], parts[1]
    url = f"https://eodhistoricaldata.com/img/logos/{exchange}/{symbol}.png"
    logo_path = os.path.join(output_dir, f"{symbol.lower()}_logo.png")
    try:
        urllib.request.urlretrieve(url, logo_path)
        if os.path.getsize(logo_path) < 100:
            os.remove(logo_path)
            return None
        return logo_path
    except: return None

class CompanyPresentationPDF(FPDF):
    """Custom PDF class with Kasona branding for Company Presentations (Landscape Slides)."""

    def __init__(self, title="Institutional Presentation", kasona_logo=None, company_logo=None, company_name=""):
        # Initialize in Landscape mode for slides
        super().__init__(orientation='L', unit='mm', format='A4')
        self.report_title = title
        self.today = datetime.now().strftime("%d.%m.%Y")
        self.kasona_logo_path = kasona_logo
        self.company_logo_path = company_logo
        self.company_name = company_name
        self.is_cover_page = True
        self.page_has_content = False
        self._register_unicode_fonts()
        self.set_auto_page_break(auto=True, margin=20)

    def add_slide(self):
        """Add a new page only if the current page has content."""
        if self.page_has_content:
            self.add_page()
            self.page_has_content = False

    def _register_unicode_fonts(self):
        self.add_font(FONT, "", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_REGULAR))
        self.add_font(FONT, "B", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_BOLD))
        self.add_font(FONT, "I", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_ITALIC))
        self.add_font(FONT, "BI", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_BOLD_ITALIC))

    def header(self):
        if self.is_cover_page or self.page_no() <= 1: return
        self.set_draw_color(*COLOR_PRIMARY_BLUE)
        self.set_line_width(0.8)
        self.line(self.l_margin, 8, self.w - self.r_margin, 8)
        self.set_font(FONT, "I", SIZE_MUTED)
        self.set_text_color(*COLOR_MUTED)
        self.set_y(10)
        self.cell(0, 5, f"KASONA INSTITUTIONAL — {self.company_name} Strategic Overview", align="L")
        if self.kasona_logo_path and os.path.exists(self.kasona_logo_path):
            self.image(self.kasona_logo_path, x=self.w - 50, y=5, h=10) # Larger logo in header
        self.ln(10)

    def footer(self):
        if self.is_cover_page: return
        self.set_y(-15)
        self.set_draw_color(*COLOR_PRIMARY_BLUE)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font(FONT, "I", SIZE_MUTED)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 5, f"Invest Analysis Portfolio | {self.today}", align="L")
        self.cell(0, 5, f"Page {self.page_no()}", align="R")

    def render_cover_page(self):
        self.is_cover_page = True
        self.add_page()
        self.page_has_content = False # Cover page doesn't count as content for next slide break
        dark_height = 140 # More dark height for landscape
        self.set_fill_color(*COLOR_COVER_BG)
        self.rect(0, 0, self.w, dark_height, 'F')
        
        self.set_y(45)
        self.set_font(FONT, "B", SIZE_TABLE)
        self.set_text_color(*COLOR_KASONA_ORANGE)
        self.cell(0, 10, "CONFIDENTIAL INSTITUTIONAL RECORD", align="C")
        self.ln(15)
        
        self.set_font(FONT, "B", SIZE_TITLE)
        self.set_text_color(*COLOR_WHITE)
        self.multi_cell(0, 15, clean_text(self.report_title).upper(), align="C")
        
        # Add company logo in center area
        logo_y = dark_height + 15
        if self.company_logo_path and os.path.exists(self.company_logo_path):
            try:
                # Maintain aspect ratio for company logo
                self.image(self.company_logo_path, x=(self.w-50)/2, y=logo_y, h=40)
            except: pass
        
        self.set_y(175)
        self.set_text_color(*COLOR_TEXT)
        self.set_font(FONT, "B", SIZE_TABLE)
        self.cell(0, 8, f"PREPARED BY KASONA INVEST ANALYSIS", align="C")
        self.ln(10)
        self.set_font(FONT, "", SIZE_BODY)
        self.cell(0, 8, f"Strategic Intelligence Unit | {self.today}", align="C")
        
        # Add Prominent Kasona Logo after text
        if self.kasona_logo_path and os.path.exists(self.kasona_logo_path):
            try:
                self.ln(15)
                self.image(self.kasona_logo_path, x=(self.w-60)/2, y=self.get_y(), h=15)
            except: pass
        
        self.set_y(-25)
        self.set_fill_color(*COLOR_LIGHT_BG)
        self.set_font(FONT, "I", SIZE_MUTED)
        self.set_text_color(*COLOR_MUTED)
        disclaimer = (
            "This document provides a structural overview of the subject company for institutional use only. "
            "It does not constitute financial advice. Accuracy is prioritized but not guaranteed."
        )
        self.set_x(self.l_margin + 20)
        self.multi_cell(self.w - 60, 5, disclaimer, fill=True, align="C")
        self.is_cover_page = False

    def write_rich_text(self, text, h=10):
        """Write rich text directly. Note: Does not handle line-wrapping as well as multi_cell."""
        text = html.unescape(text)
        text = strip_emoji(text)
        parts = re.split(r'(\*\*.*?\*\*|\[.*?\]\(.*?\))', text)
        for part in parts:
            if not part: continue
            if part.startswith('**'):
                self.set_font(FONT, "B", self.font_size_pt)
                self.write(h, part[2:-2])
            elif part.startswith('['):
                match = re.match(r'\[(.*?)\]\((.*?)\)', part)
                if match:
                    self.set_text_color(*COLOR_PRIMARY_BLUE)
                    self.write(h, match.group(1), link=match.group(2))
                    self.set_text_color(*COLOR_TEXT)
            else:
                self.set_font(FONT, "", self.font_size_pt)
                self.write(h, part)

    def write_paragraph(self, text, h=8, indent=0):
        """Write a full paragraph with proper wrapping and optional indentation."""
        self.set_x(self.l_margin + indent)
        w = self.w - self.r_margin - self.get_x()
        
        if "**" not in text and "[" not in text:
            # Plain text: use multi_cell for perfect wrapping
            self.set_font(FONT, "", SIZE_BODY)
            self.multi_cell(w, h, clean_text(text))
        else:
            # Rich text: use write_rich_text (may still have overlapping if word too long)
            self.write_rich_text(text, h=h)
            self.ln(h + 2)
        self.page_has_content = True

    def render_table(self, table_lines):
        """Render a Markdown table as a professional slide table."""
        if not table_lines: return
        rows = []
        for line in table_lines:
            if not line.strip().startswith("|"): continue
            if ":---" in line or "|---" in line: continue
            cells = [clean_text(c) for c in line.split("|") if c.strip() or (line.startswith("|") and line.endswith("|"))]
            if line.startswith("|") and not cells[0]: cells = cells[1:]
            if line.endswith("|") and not cells[-1]: cells = cells[:-1]
            if cells: rows.append(cells)
            
        if not rows: return
        
        if self.get_y() > 160:
            self.add_slide()

        self.set_font(FONT, "B", SIZE_TABLE)
        col_width = (self.w - self.l_margin - self.r_margin) / len(rows[0])
        
        self.set_fill_color(*COLOR_TABLE_HEADER)
        self.set_text_color(*COLOR_WHITE)
        for cell in rows[0]:
            self.cell(col_width, 10, cell, border=1, align="C", fill=True)
        self.ln()
        
        self.set_font(FONT, "", SIZE_TABLE)
        self.set_text_color(*COLOR_TEXT)
        for i, row in enumerate(rows[1:]):
            fill = (i % 2 == 0)
            self.set_fill_color(*COLOR_LIGHT_BG)
            for cell in row:
                self.cell(col_width, 10, cell, border=1, align="C", fill=fill)
            self.ln()
        self.ln(5)
        self.page_has_content = True

    def render_image_slide(self, image_source, caption=""):
        """Embed an image into the current slide, supporting local paths and web URLs."""
        image_path = image_source
        is_temp = False
        
        if image_source.startswith("http"):
            try:
                fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                req = urllib.request.Request(image_source, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(temp_path, 'wb') as out_file:
                    out_file.write(response.read())
                image_path = temp_path
                is_temp = True
            except Exception as e:
                print(f"Error downloading image {image_source}: {e}")
                return

        if not os.path.exists(image_path): return
        
        self.add_slide()
        self.ln(5)
        try:
            img_h = 110
            self.set_y(40)
            # Center horizontally. w=297, scale image to fit width or height.
            self.image(image_path, x=(self.w-180)/2, y=self.get_y(), h=img_h)
            self.set_y(self.get_y() + img_h + 5)
            if caption:
                self.set_font(FONT, "I", SIZE_MUTED)
                self.cell(0, 8, caption, align="C")
                self.ln(10)
        except Exception as e:
            print(f"Error rendering image: {e}")
        
        if is_temp:
            try: os.remove(image_path)
            except: pass
            
        self.page_has_content = True

def convert_md_to_pdf(md_path, output_dir, ticker=None, kasona_logo=None):
    content = md_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    title = md_path.stem
    for line in lines:
        if line.startswith("# "):
            title = clean_text(line[2:])
            break
    company_name = title.split(":")[1].strip() if ":" in title else title
    company_logo = download_company_logo(ticker, str(output_dir)) if ticker else None

    pdf = CompanyPresentationPDF(title=title, kasona_logo=kasona_logo, company_logo=company_logo, company_name=company_name)
    pdf.alias_nb_pages()
    pdf.render_cover_page()
    
    # After cover page, start first content slide
    pdf.add_page()
    pdf.page_has_content = False 

    skip_h1 = True
    in_table = False
    table_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if "## [SUBSKILL] Neural Audio Briefing Script" in stripped:
            break
            
        if not stripped:
            if in_table:
                pdf.render_table(table_lines)
                table_lines = []
                in_table = False
            continue

        if stripped == "---":
            pdf.add_slide()
            continue

        img_match = re.match(r'!\[(.*?)\]\((.*?)\)', stripped)
        if img_match:
            caption, source = img_match.groups()
            pdf.render_image_slide(source, caption)
            continue

        if stripped.startswith("# ") and skip_h1:
            skip_h1 = False
            continue

        if stripped.startswith("## "):
            if in_table:
                pdf.render_table(table_lines)
                table_lines = []
                in_table = False
            
            pdf.add_slide()
            pdf.ln(10)
            pdf.set_font(FONT, "B", SIZE_HEADER)
            pdf.set_text_color(*COLOR_PRIMARY_BLUE)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 12, clean_text(stripped[3:]))
            pdf.set_draw_color(*COLOR_BORDER)
            pdf.line(pdf.l_margin, pdf.get_y()+2, pdf.w-pdf.r_margin, pdf.get_y()+2)
            pdf.ln(12)
            continue

        if stripped.startswith("### "):
            if in_table:
                pdf.render_table(table_lines)
                table_lines = []
                in_table = False

            # More aggressive slide break to keep sub-headers with their content
            if pdf.get_y() > 165: pdf.add_slide()
            else: pdf.ln(5) # Add space from previous content
            
            pdf.set_font(FONT, "B", SIZE_BODY)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 10, clean_text(stripped[4:]))
            pdf.ln(4)
            pdf.page_has_content = True
            continue

        if stripped.startswith("|"):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            pdf.render_table(table_lines)
            table_lines = []
            in_table = False

        if stripped.startswith("- "):
            if pdf.get_y() > 185: pdf.add_slide()
            pdf.set_font(FONT, "", SIZE_BODY)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_x(pdf.l_margin + 10)
            bullet = chr(8226) + " "
            pdf.write(10, bullet)
            pdf.write_paragraph(stripped[2:], h=10, indent=15)
        else:
            if pdf.get_y() > 185: pdf.add_slide()
            pdf.set_font(FONT, "", SIZE_BODY)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.write_paragraph(stripped, h=10, indent=0)

    if in_table:
        pdf.render_table(table_lines)

    pdf_path = output_dir / (md_path.stem + ".pdf")
    pdf.output(str(pdf_path))
    return pdf_path

    if in_table:
        pdf.render_table(table_lines)

    pdf_path = output_dir / (md_path.stem + ".pdf")
    pdf.output(str(pdf_path))
    return pdf_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--ticker")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    
    md_path = Path(args.file).resolve()
    output_dir = Path(args.output_dir) if args.output_dir else md_path.parent
    logo_path = Path(__file__).parent.parent / "resources" / "kasona_logo.jpg"
    
    pdf_path = convert_md_to_pdf(md_path, output_dir, args.ticker, str(logo_path) if logo_path.exists() else None)
    print(f"Created: {pdf_path}")

if __name__ == "__main__":
    main()
