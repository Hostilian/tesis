import os
import re
from fpdf import FPDF

class ThesisPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 9)
            self.set_text_color(100, 100, 100)
            self.cell(120, 10, "Space-Based Economic Intelligence — Eren Ozturk", 0, new_x="RIGHT", new_y="TOP", align="L")
            self.cell(70, 10, f"Page {self.page_no()}", 0, new_x="LMARGIN", new_y="NEXT", align="R")
            self.line(10, 18, 200, 18)
            self.ln(5)

    def footer(self):
        pass

def compile_pdf():
    pdf = ThesisPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Load fonts supporting Czech characters from Windows Fonts folder
    font_path = r"C:\Windows\Fonts\arial.ttf"
    font_bold = r"C:\Windows\Fonts\arialbd.ttf"
    font_italic = r"C:\Windows\Fonts\ariali.ttf"
    
    pdf.add_font("Arial", "", font_path)
    pdf.add_font("Arial", "B", font_bold)
    pdf.add_font("Arial", "I", font_italic)
    
    # ── COVER PAGE ──
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "CZECH UNIVERSITY OF LIFE SCIENCES PRAGUE", 0, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Faculty of Economics and Management", 0, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, "Department of Informatics (KII)", 0, new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.ln(40)
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(0, 12, "Space-Based Economic Intelligence:\nDetecting Hidden Resource Anomalies Using Open Satellite APIs", 0, "C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Arial", "", 14)
    pdf.cell(0, 10, "BACHELOR THESIS", 0, new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.ln(60)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Author: Eren Ozturk (XOZTE001@studenti.czu.cz)", 0, new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.cell(0, 8, "Supervisor: Dr. Jirí Brožek", 0, new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.cell(0, 8, "Academic Year: 2025–2026", 0, new_x="LMARGIN", new_y="NEXT", align="L")
    
    pdf.ln(20)
    pdf.cell(0, 10, "Prague, 2026", 0, new_x="LMARGIN", new_y="NEXT", align="C")
    
    # ── ABSTRACT PAGE ──
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, "Abstract", 0, new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    pdf.set_font("Arial", "", 11)
    abstract_text = (
        "This thesis investigates the implementation of space-based economic intelligence systems "
        "using civilian satellite APIs. By constructing an automated pipeline querying Google Earth Engine "
        "and Copernicus Data Space Ecosystem collections, spectral anomalies are extracted and analyzed "
        "via unsupervised Isolation Forests and temporal Z-scores. The resulting dashboard provides a "
        "practical Decision Support System (DSS) demonstrating real-world applications in monitoring "
        "lithium brine evaporation ponds in Chile, informal gold mining deforestation in Peru, and "
        "industrial night-light changes in the Czech Republic."
    )
    pdf.multi_cell(0, 6, abstract_text, new_x="LMARGIN", new_y="NEXT")
    
    # ── CHAPTERS ──
    chapters_dir = r"d:\CODING\tesis\thesis\chapters"
    files = [
        "01_introduction.md",
        "02_literature_review.md",
        "03_methodology.md",
        "04_system_design.md",
        "05_results.md",
        "06_discussion.md",
        "07_conclusion.md",
        "appendix_a_repo.md",
        "appendix_b_apis.md",
        "appendix_c_metadata.md",
        "appendix_d_vis.md",
        "appendix_e_glossary.md",
        "appendix_f_acronyms.md"
    ]
    
    for filename in files:
        filepath = os.path.join(chapters_dir, filename)
        if not os.path.exists(filepath):
            continue
            
        print(f"Processing chapter file: {filename}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        pdf.add_page()
        lines = content.split("\n")
        
        # Parse and write content line by line
        in_table = False
        table_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check for tables
            if line_stripped.startswith("|"):
                in_table = True
                table_lines.append(line_stripped)
                continue
            else:
                if in_table:
                    render_pdf_table(pdf, table_lines)
                    table_lines = []
                    in_table = False
            
            if not line_stripped:
                pdf.ln(3)
                continue
                
            # Headers
            if line_stripped.startswith("# "):
                title = line_stripped[2:]
                pdf.set_font("Arial", "B", 16)
                pdf.set_text_color(0, 51, 102)
                pdf.multi_cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)
                pdf.ln(5)
            elif line_stripped.startswith("## "):
                title = line_stripped[3:]
                pdf.set_font("Arial", "B", 13)
                pdf.set_text_color(51, 102, 153)
                pdf.multi_cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)
            elif line_stripped.startswith("### "):
                title = line_stripped[4:]
                pdf.set_font("Arial", "B", 11)
                pdf.multi_cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            elif line_stripped.startswith("#### "):
                title = line_stripped[5:]
                pdf.set_font("Arial", "BI", 11)
                pdf.multi_cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            # List items
            elif line_stripped.startswith("- ") or line_stripped.startswith("* "):
                bullet_text = line_stripped[2:]
                pdf.set_font("Arial", "", 10)
                clean_text = "  • " + parse_markdown_style(bullet_text)
                pdf.multi_cell(0, 6, clean_text, new_x="LMARGIN", new_y="NEXT")
            # Normal paragraph
            else:
                pdf.set_font("Arial", "", 10)
                clean_text = parse_markdown_style(line_stripped)
                pdf.multi_cell(0, 5, clean_text, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                
        if in_table:
            render_pdf_table(pdf, table_lines)
            
    output_path = r"d:\CODING\tesis\thesis\thesis.pdf"
    pdf.output(output_path)
    print(f"Thesis PDF compiled successfully at: {output_path}")

def parse_markdown_style(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    return text

def render_pdf_table(pdf, table_lines):
    if len(table_lines) < 2:
        return
        
    headers = [c.strip() for c in table_lines[0].split("|")[1:-1]]
    if not headers or len(headers) == 0:
        pdf.set_font("Arial", "", 10)
        for tl in table_lines:
            pdf.multi_cell(0, 5, tl, new_x="LMARGIN", new_y="NEXT")
        return
        
    rows = []
    for r in table_lines[2:]:
        row_cells = [c.strip() for c in r.split("|")[1:-1]]
        if row_cells:
            rows.append(row_cells)
            
    pdf.set_font("Arial", "B", 9)
    col_width = 190 / len(headers)
    
    # Render headers
    for h in headers:
        pdf.cell(col_width, 8, h[:30], 1, new_x="RIGHT", new_y="TOP", align="C")
    pdf.ln(8)
    
    # Render rows
    pdf.set_font("Arial", "", 8)
    for r in rows:
        for val in r:
            pdf.cell(col_width, 8, val[:40], 1, new_x="RIGHT", new_y="TOP", align="L")
        pdf.ln(8)
    pdf.ln(4)

if __name__ == "__main__":
    compile_pdf()
