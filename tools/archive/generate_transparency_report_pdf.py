import sys
from fpdf import FPDF
from pathlib import Path

class TransparencyPDF(FPDF):
    def header(self):
        self.set_font('Courier', 'B', 12)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, 'Kasona Institutional Research - Data Transparency Report', 0, 1, 'L')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Courier', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(markdown_path, output_path):
    pdf = TransparencyPDF()
    pdf.add_page()
    pdf.set_font('Courier', '', 12)
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Courier', 'B', 24)
    pdf.cell(0, 20, 'Data Transparency Report', 0, 1, 'C', fill=True)
    pdf.ln(10)
    
    # Define width for multi_cell (page width minus margins)
    w = pdf.w - 2 * pdf.l_margin
    
    pdf.set_text_color(15, 23, 42)
    for line in lines:
        line = line.rstrip() # Keep leading spaces for markdown indentation if needed
        if not line:
            pdf.ln(5)
            continue
            
        if line.startswith('# '):
            pdf.set_font('Courier', 'B', 18)
            pdf.cell(w, 15, line[2:], 0, 1, 'L')
            pdf.ln(5)
        elif line.startswith('## '):
            pdf.set_font('Courier', 'B', 14)
            pdf.cell(w, 12, line[3:], 0, 1, 'L')
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font('Courier', 'B', 12)
            pdf.cell(w, 10, line[4:], 0, 1, 'L')
            pdf.ln(1)
        elif line.startswith('```'):
            pdf.set_font('Courier', 'I', 10)
            pdf.set_text_color(100, 116, 139)
        elif line.startswith('---'):
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.l_margin, pdf.get_y())
            pdf.ln(5)
        else:
            pdf.set_font('Courier', '', 11)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(w, 8, line)

    pdf.output(output_path)
    print(f"PDF generated: {output_path}")

if __name__ == "__main__":
    markdown_file = sys.argv[1]
    output_file = sys.argv[2]
    create_pdf(markdown_file, output_file)
