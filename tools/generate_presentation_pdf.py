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
SIZE_TITLE = 32
SIZE_HEADER = 24
SIZE_SUBHEADER = 18
SIZE_BODY = 14
SIZE_TABLE = 12
SIZE_MUTED = 9

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
    """Download company logo from EODHD with robust symbol handling."""
    parts = ticker.split(".")
    if len(parts) != 2: return None
    symbol, exchange = parts[0], parts[1]
    
    # Try with full symbol, then base symbol (e.g. BERG-B -> BERG)
    symbols_to_try = [symbol, symbol.split("-")[0]]
    
    for s in symbols_to_try:
        url = f"https://eodhistoricaldata.com/img/logos/{exchange}/{s}.png"
        logo_path = os.path.join(output_dir, f"{s.lower()}_logo.png")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    with open(logo_path, 'wb') as f:
                        f.write(response.read())
                    if os.path.getsize(logo_path) > 100:
                        return logo_path
        except:
            continue
    return None

class CompanyPresentationPDF(FPDF):
    """Custom PDF class with Kasona branding for Company Presentations (Landscape Slides)."""

    def __init__(self, title="Institutional Presentation", kasona_logo=None, company_logo=None, company_name=""):
        # Initialize in Portrait mode for documents
        super().__init__(orientation='P', unit='mm', format='A4')
        self.report_title = title
        self.today = datetime.now().strftime("%d.%m.%Y")
        self.kasona_logo_path = kasona_logo
        self.company_logo_path = company_logo
        self.company_name = company_name
        self.is_cover_page = True
        self.page_has_content = False
        self._register_unicode_fonts()
        self.set_auto_page_break(auto=True, margin=20)

    def add_page(self, *args, **kwargs):
        """Override add_page to track content state."""
        super().add_page(*args, **kwargs)
        self.page_has_content = False

    def add_slide(self):
        """Add a new page only if the current page has content to prevent blank pages."""
        if self.page_has_content:
            self.add_page()
            return True
        return False

    def _register_unicode_fonts(self):
        self.add_font(FONT, "", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_REGULAR))
        self.add_font(FONT, "B", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_BOLD))
        self.add_font(FONT, "I", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_ITALIC))
        self.add_font(FONT, "BI", os.path.join(UNICODE_FONT_DIR, UNICODE_FONT_BOLD_ITALIC))

    def header(self):
        # Only skip header on the actual cover page
        if self.is_cover_page: return
        
        self.set_y(12)
        self.set_font(FONT, "I", SIZE_MUTED)
        self.set_text_color(*COLOR_MUTED)
        self.cell(0, 5, f"KASONA INSTITUTIONAL — {self.company_name}", align="L")
        
        # Consistent Kasona Logo in Header
        if self.kasona_logo_path and os.path.exists(self.kasona_logo_path):
            try:
                self.image(self.kasona_logo_path, x=self.w - 35, y=8, h=6)
            except: pass
        
        self.set_draw_color(*COLOR_PRIMARY_BLUE)
        self.set_line_width(0.3)
        self.line(self.l_margin, 16, self.w - self.r_margin, 16)
        self.ln(8)

    def add_section(self, title, content):
        if not content or str(content).strip() == "":
            return # Should not happen with ZNCR

        title_upper = title.upper()
        
        # Color Coding for Bull/Bear cases
        accent_color = COLOR_PRIMARY_BLUE
        if "BULL" in title_upper:
            accent_color = (34, 197, 94) # Green-600
        elif "BEAR" in title_upper:
            accent_color = (239, 68, 68)  # Red-600
            
        self.set_font(FONT, "B", SIZE_SUBHEADER)
        self.set_text_color(*accent_color)
        self.cell(0, 10, title_upper, ln=True)
        
        self.set_draw_color(*accent_color)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 40, self.get_y())
        self.ln(5)
        
        self.set_font(FONT, "", SIZE_BODY)
        self.set_text_color(*COLOR_DARK)
        self.multi_cell(0, 8, strip_emoji(str(content)), align="L")
        self.ln(12)

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
        # Cover page background
        dark_height = 180 
        self.set_fill_color(*COLOR_COVER_BG)
        self.rect(0, 0, self.w, dark_height, 'F')
        
        # Kasona logo at TOP of cover (inside dark band)
        if self.kasona_logo_path and os.path.exists(self.kasona_logo_path):
            try:
                self.image(self.kasona_logo_path, x=(self.w - 40) / 2, y=12, h=10)
            except:
                pass
        
        self.set_y(38)
        self.set_font(FONT, "B", SIZE_TABLE)
        self.set_text_color(*COLOR_KASONA_ORANGE)
        self.cell(0, 10, "CONFIDENTIAL INSTITUTIONAL RECORD", align="C")
        self.ln(15)
        
        self.set_font(FONT, "B", SIZE_TITLE)
        self.set_text_color(*COLOR_WHITE)
        self.multi_cell(0, 15, clean_text(self.report_title).upper(), align="C")
        
        # Company Logo: Smaller and precisely centered on the page
        logo_h = 25
        logo_y = (self.h - logo_h) / 2
        if self.company_logo_path and os.path.exists(self.company_logo_path):
            try:
                # Position centered horizontally and vertically
                self.image(self.company_logo_path, x=(self.w - 50) / 2, y=logo_y, w=50)
            except Exception as e:
                print(f"[DEBUG] Cover logo error: {e}")
        
        self.set_y(265) # Start text below logo
        self.set_text_color(*COLOR_TEXT)
        self.set_font(FONT, "B", SIZE_TABLE)
        self.cell(0, 8, f"PREPARED BY KASONA INVEST ANALYSIS", align="C")
        self.ln(6)
        self.set_font(FONT, "", SIZE_BODY)
        self.cell(0, 8, f"Strategic Intelligence Unit | {self.today}", align="C")
        
        if self.kasona_logo_path and os.path.exists(self.kasona_logo_path):
            try:
                self.ln(12)
                self.image(self.kasona_logo_path, x=(self.w-50)/2, y=self.get_y(), h=12)
            except: pass
        
        self.is_cover_page = False

    def render_last_page(self):
        """Add the final page with disclaimer and Kasona production branding."""
        self.is_cover_page = False # Ensure footer shows
        
        # Only add a slide if we're not already on a fresh page
        if self.page_has_content:
            self.add_page()
        
        # Now we are on a fresh page for the conclusion branding
        self.set_y(60)
        
        # Center Branding
        if self.kasona_logo_path and os.path.exists(self.kasona_logo_path):
            self.image(self.kasona_logo_path, x=(self.w-60)/2, y=self.get_y(), h=15)
            self.ln(20)
            
        self.set_font(FONT, "B", SIZE_HEADER)
        self.set_text_color(*COLOR_PRIMARY_BLUE)
        self.cell(0, 15, "A Kasona Production", align="C")
        self.ln(15)
        
        self.set_font(FONT, "", SIZE_BODY)
        self.set_text_color(*COLOR_TEXT)
        self.cell(0, 10, "The solution for independent investors", align="C")
        self.ln(10)
        
        # Link
        self.set_font(FONT, "U", SIZE_BODY)
        self.set_text_color(*COLOR_PRIMARY_BLUE)
        self.cell(0, 10, "www.kasona.ai", link="https://www.kasona.ai/", align="C")
        self.ln(40)
        
        # Disclaimer Box
        self.set_fill_color(*COLOR_LIGHT_BG)
        self.set_font(FONT, "I", SIZE_MUTED)
        self.set_text_color(*COLOR_MUTED)
        disclaimer = (
            "DISCLAIMER: This report is for informational purposes only and does not constitute investment advice. "
            "All analysis is AI-generated and subject to verification. Precision is intended but not guaranteed. "
            "Past performance is not indicative of future results."
        )
        self.set_x(self.l_margin + 15)
        self.multi_cell(self.w - 50, 5, disclaimer, border=1, fill=True, align="C")

    def write_rich_text(self, text, h=7):
        """Write rich text directly with tightened spacing."""
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
                    label = match.group(1)
                    url = match.group(2).strip()
                    if url:
                        self.set_text_color(*COLOR_PRIMARY_BLUE)
                        self.write(h, label, link=url)
                        self.set_text_color(*COLOR_TEXT)
                    else:
                        self.write(h, label)
            else:
                self.set_font(FONT, "", self.font_size_pt)
                self.write(h, part)

    def write_paragraph(self, text, h=7, indent=0):
        """Write a paragraph with tightened line height."""
        self.set_x(self.l_margin + indent)
        w = self.w - self.r_margin - self.get_x()
        
        if "**" not in text and "[" not in text:
            self.set_font(FONT, "", SIZE_BODY)
            self.multi_cell(w, h, clean_text(text))
        else:
            self.write_rich_text(text, h=h)
            self.ln(h + 1)
        self.page_has_content = True

    def render_table(self, table_lines):
        """Render a Markdown table as a professional table."""
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
        
        if self.get_y() > 240: # Adjusted for portrait
            self.add_slide()

        self.set_font(FONT, "B", SIZE_TABLE)
        col_width = (self.w - self.l_margin - self.r_margin) / len(rows[0])
        
        self.set_fill_color(*COLOR_TABLE_HEADER)
        self.set_text_color(*COLOR_WHITE)
        for cell in rows[0]:
            self.cell(col_width, 8, cell, border=1, align="C", fill=True)
        self.ln()
        
        self.set_font(FONT, "", SIZE_TABLE)
        self.set_text_color(*COLOR_TEXT)
        for i, row in enumerate(rows[1:]):
            fill = (i % 2 == 0)
            self.set_fill_color(*COLOR_LIGHT_BG)
            for cell in row:
                self.cell(col_width, 8, cell, border=1, align="C", fill=fill)
            self.ln()
        self.ln(4)
        self.page_has_content = True

    def render_image_slide(self, image_source, caption=""):
        """Embed an image with centering for portrait mode."""
        image_path = image_source
        is_temp = False
        
        if image_source.startswith("file:///"):
            image_path = image_source[8:]
        elif image_source.startswith("file://"):
            image_path = image_source[7:]
        
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

        if not os.path.exists(image_path):
            print(f"[WARN] Image not found: {image_path}")
            return
        
        img_w = 170 # Fixed width for centering in 210mm
        # Calculate height from aspect ratio using PIL to prevent overlaps
        img_h = 100 # Default if PIL fails
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                w, h = img.size
                aspect = h / w
                img_h = img_w * aspect
        except Exception as e:
            print(f"[DEBUG] Image dimension error: {e}")
        
        self.ln(5)
        try:
            # Check if image fits on page, else start new
            if self.get_y() + img_h > 260:
                self.add_slide()
            
            self.image(image_path, x=(self.w-img_w)/2, y=self.get_y(), w=img_w) 
            self.set_y(self.get_y() + img_h + 8) # Move cursor below image accurately
            
            if caption:
                self.set_font(FONT, "I", SIZE_MUTED)
                self.cell(0, 6, clean_text(caption), align="C")
                self.ln(8)
        except Exception as e:
            print(f"Error rendering image: {e}")
        
        if is_temp:
            try: os.remove(image_path)
            except: pass
            
        self.page_has_content = True

def convert_md_to_pdf(md_path, output_dir, ticker=None, kasona_logo=None, company_logo_manual=None):
    content = md_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    title = md_path.stem
    for line in lines:
        if line.startswith("# "):
            title = clean_text(line[2:])
            break
    company_name = title.split(":")[1].strip() if ":" in title else title
    
    if company_logo_manual and os.path.exists(company_logo_manual):
        company_logo = company_logo_manual
    else:
        company_logo = download_company_logo(ticker, str(output_dir)) if ticker else None

    pdf = CompanyPresentationPDF(title=title, kasona_logo=kasona_logo, company_logo=company_logo, company_name=company_name)
    pdf.alias_nb_pages()
    pdf.render_cover_page()
    
    # Crucial: after cover, we are ready for content
    pdf.is_cover_page = False
    pdf.page_has_content = False 

    # Check for images in content
    has_images = any(re.match(r'!\[(.*?)\]\((.*?)\)', line.strip()) for line in lines)
    injected_image = False
    default_image = Path(__file__).parent.parent / "resources" / "visuals" / "industrial_1.png"

    skip_h1 = True
    in_table = False
    table_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Automatic Image Injection: after the first section (usually history)
        if not has_images and not injected_image and stripped.startswith("## ") and i > 20:
             if default_image.exists():
                 pdf.render_image_slide(str(default_image), "Strategic Industrial Context")
                 injected_image = True
        
        if not stripped:
            if in_table:
                pdf.render_table(table_lines)
                table_lines = []
                in_table = False
            continue

        if stripped == "---":
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
            
            # Break for H2 if lower on page
            if pdf.get_y() > 140:
                pdf.add_slide()
            
            pdf.ln(8)
            pdf.set_font(FONT, "B", SIZE_HEADER)
            pdf.set_text_color(*COLOR_PRIMARY_BLUE)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 10, clean_text(stripped[3:]))
            pdf.set_draw_color(*COLOR_BORDER)
            pdf.line(pdf.l_margin, pdf.get_y()+1, pdf.w-pdf.r_margin, pdf.get_y()+1)
            pdf.ln(8)
            continue

        if stripped.startswith("### "):
            if in_table:
                pdf.render_table(table_lines)
                table_lines = []
                in_table = False

            if pdf.get_y() > 240: pdf.add_slide()
            else: pdf.ln(4)
            
            pdf.set_font(FONT, "B", SIZE_BODY)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 8, clean_text(stripped[4:]))
            pdf.ln(2)
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
            if pdf.get_y() > 260: pdf.add_slide()
            pdf.set_font(FONT, "", SIZE_BODY)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_x(pdf.l_margin + 10)
            bullet = chr(8226) + " "
            pdf.write(7, bullet)
            pdf.write_paragraph(stripped[2:], h=7, indent=15)
        else:
            if pdf.get_y() > 260: pdf.add_slide()
            pdf.set_font(FONT, "", SIZE_BODY)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.write_paragraph(stripped, h=7, indent=0)

    # Render Conclusion Page
    pdf.render_last_page()

    pdf_path = output_dir / (md_path.stem + ".pdf")
    pdf.output(str(pdf_path))
    return pdf_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--ticker")
    parser.add_argument("--output-dir")
    parser.add_argument("--company-logo")
    args = parser.parse_args()
    
    md_path = Path(args.file).resolve()
    output_dir = Path(args.output_dir) if args.output_dir else md_path.parent
    logo_path = Path(__file__).parent.parent / "resources" / "kasona_logo.jpg"
    
    pdf_path = convert_md_to_pdf(md_path, output_dir, args.ticker, str(logo_path) if logo_path.exists() else None, args.company_logo)
    print(f"Created: {pdf_path}")

if __name__ == "__main__":
    main()
