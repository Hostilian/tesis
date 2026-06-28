import os
import re

def markdown_to_latex(md_content):
    # Strip the top level heading (e.g. # Chapter 1: Introduction)
    lines = md_content.split('\n')
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    md_content = '\n'.join(lines)
    
    # Strip Section 2.10 if present (Bibliography list, since LaTeX handles this automatically)
    if "## 2.10" in md_content:
        md_content = md_content.split("## 2.10")[0]
    
    # Replace markdown bold **text** with \textbf{text}
    md_content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', md_content)
    
    # Replace markdown italic *text* with \textit{text}
    # Be careful not to match list items
    md_content = re.sub(r'(?<!\S)\*(?!\s)(.*?)\*', r'\\textit{\1}', md_content)
    
    # Replace inline code `code` with \texttt{code}
    md_content = re.sub(r'`(.*?)`', r'\\texttt{\1}', md_content)
    
    # Convert citation markers [R2xx] or [R2xx, R2yy] to \cite{R2xx, R2yy}
    md_content = re.sub(r'\[(R2\d+(?:\s*,\s*R2\d+)*)\]', lambda m: '\\cite{' + ', '.join(p.strip() for p in m.group(1).split(',')) + '}', md_content)
    
    # Replace headers
    # ## Section -> \section{Section}
    # ### Subsection -> \subsection{Subsection}
    # #### Subsubsection -> \subsubsection{Subsubsection}
    def replace_headers(match):
        level = len(match.group(1))
        title = match.group(2).strip()
        # Remove numbers from title like "1.1 Background" to let LaTeX handle numbering
        title = re.sub(r'^[0-9\.]+\s+', '', title)
        if level == 2:
            return f"\\section{{{title}}}"
        elif level == 3:
            return f"\\subsection{{{title}}}"
        else:
            return f"\\subsubsection{{{title}}}"
            
    md_content = re.sub(r'^(#{2,4})\s+(.*)$', replace_headers, md_content, flags=re.MULTILINE)
    
    # Escape special characters like %, _, & that are not part of LaTeX commands
    # For now, let's escape %, _, & safely
    md_content = re.sub(r'(?<!\\)%', r'\\%', md_content)
    md_content = re.sub(r'(?<!\\)_', r'\\_', md_content)
    md_content = re.sub(r'(?<!\\)&', r'\\&', md_content)
    
    # Lists
    # Bullet lists: lines starting with - or * or +
    lines = md_content.split('\n')
    in_list = False
    list_type = None # 'itemize' or 'enumerate'
    new_lines = []
    
    for line in lines:
        bullet_match = re.match(r'^\s*[\-\*\+]\s+(.*)$', line)
        enum_match = re.match(r'^\s*\d+\.\s+(.*)$', line)
        
        if bullet_match:
            if not in_list or list_type != 'itemize':
                if in_list:
                    new_lines.append(f"\\end{{{list_type}}}")
                new_lines.append("\\begin{itemize}")
                in_list = True
                list_type = 'itemize'
            item_text = bullet_match.group(1)
            new_lines.append(f"  \\item {item_text}")
        elif enum_match:
            if not in_list or list_type != 'enumerate':
                if in_list:
                    new_lines.append(f"\\end{{{list_type}}}")
                new_lines.append("\\begin{enumerate}")
                in_list = True
                list_type = 'enumerate'
            item_text = enum_match.group(1)
            new_lines.append(f"  \\item {item_text}")
        else:
            if in_list and (line.startswith('  ') or line.startswith('\t') or line.strip() == ''):
                new_lines.append(line)
            else:
                if in_list:
                    new_lines.append(f"\\end{{{list_type}}}")
                    in_list = False
                    list_type = None
                new_lines.append(line)
            
    if in_list:
        new_lines.append(f"\\end{{{list_type}}}")
        
    md_content = '\n'.join(new_lines)
    
    # Convert markdown tables to LaTeX tabular
    table_pattern = re.compile(r'((?:^\|.*\|$\n?)+)', re.MULTILINE)
    
    def convert_table(match):
        table_lines = match.group(1).strip().split('\n')
        if len(table_lines) < 2:
            return match.group(1)
            
        # Parse headers and alignments
        headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        alignments = [c.strip() for c in table_lines[1].split('|')[1:-1]]
        
        col_count = len(headers)
        col_spec = ""
        for a in alignments:
            if a.startswith(':') and a.endswith(':'):
                col_spec += 'c'
            elif a.endswith(':'):
                col_spec += 'r'
            else:
                col_spec += 'l'
                
        latex_table = []
        latex_table.append(f"\\begin{{table}}[h]")
        latex_table.append(f"\\centering")
        latex_table.append(f"\\begin{{tabular}}{{{col_spec}}}")
        latex_table.append(f"\\toprule")
        latex_table.append(" & ".join(headers) + " \\\\")
        latex_table.append(f"\\midrule")
        
        for row_line in table_lines[2:]:
            cols = [c.strip() for c in row_line.split('|')[1:-1]]
            if len(cols) == col_count:
                latex_table.append(" & ".join(cols) + " \\\\")
                
        latex_table.append(f"\\bottomrule")
        latex_table.append(f"\\end{{tabular}}")
        latex_table.append(f"\\end{{table}}")
        return "\n".join(latex_table)
        
    md_content = table_pattern.sub(convert_table, md_content)
    
    # Replace markdown link syntax [text](url) with \href{url}{text}
    md_content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\\href{\2}{\1}', md_content)
    
    return md_content

def main():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "chapters"))
    dest_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "latex", "chapters"))
    
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Converting markdown files from {src_dir} to LaTeX in {dest_dir}...")
    
    files = [f for f in os.listdir(src_dir) if f.endswith('.md')]
    for file in files:
        src_path = os.path.join(src_dir, file)
        dest_file = file[:-3] + ".tex"
        dest_path = os.path.join(dest_dir, dest_file)
        
        print(f"Converting {file} -> {dest_file}...")
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        latex_content = markdown_to_latex(content)
        
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
            
    print("Conversion complete!")

if __name__ == "__main__":
    main()
