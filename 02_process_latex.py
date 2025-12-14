#!/usr/bin/env python
import os
import re
import glob
import json
from pathlib import Path
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import regex
from pylatexenc.latex2text import LatexNodes2Text
import pdfplumber

class LatexProcessor:
    """Process LaTeX files for LLM training."""
    
    def __init__(self, source_dir, output_dir):
        """Initialize the LaTeX processor."""
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.citations = {}
        self.figures = {}
        self.tables = {}
        self.section_structure = []

    def find_main_tex_file(self, reference_dir):
        """Find the main .tex file in the directory."""
        tex_files = list(reference_dir.glob("*.tex"))
        
        # If only one .tex file exists, return it
        if len(tex_files) == 1:
            return tex_files[0]
        
        # Look for files that might be the main file
        potential_main_files = []
        for tex_file in tex_files:
            with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Check for documentclass or begin{document}
                if '\\documentclass' in content and '\\begin{document}' in content:
                    potential_main_files.append(tex_file)
        
        if len(potential_main_files) == 1:
            return potential_main_files[0]
        elif len(potential_main_files) > 1:
            # If multiple main files, look for the one that includes others
            for tex_file in potential_main_files:
                with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if '\\input{' in content or '\\include{' in content:
                        return tex_file
            
            # If no clear indication, use the largest file
            return max(potential_main_files, key=os.path.getsize)
        
        # If no main file identified, use the largest .tex file
        if tex_files:
            return max(tex_files, key=lambda x: os.path.getsize(x))
        
        return None

    def extract_bib_entries(self, reference_dir):
        """Extract bibliography entries from .bib files."""
        bib_files = list(reference_dir.glob("*.bib"))
        
        all_entries = {}
        
        for bib_file in bib_files:
            try:
                with open(bib_file, 'r', encoding='utf-8', errors='ignore') as bibtex_file:
                    parser = BibTexParser()
                    parser.customization = convert_to_unicode
                    bib_database = bibtexparser.load(bibtex_file, parser=parser)
                    
                    for entry in bib_database.entries:
                        key = entry.get('ID', '')
                        if key:
                            authors = entry.get('author', 'Unknown Author')
                            title = entry.get('title', 'Unknown Title')
                            year = entry.get('year', '')
                            journal = entry.get('journal', '')
                            
                            all_entries[key] = {
                                'authors': authors,
                                'title': title,
                                'year': year,
                                'journal': journal
                            }
            except Exception as e:
                print(f"Error processing {bib_file}: {str(e)}")
                
        return all_entries

    def extract_citations(self, content):
        """Extract citation keys from content."""
        citation_pattern = r'\\cite(?:\[.*?\])?{([^}]*)}'
        citation_matches = re.finditer(citation_pattern, content)
        
        citations = {}
        for match in citation_matches:
            citation_keys = match.group(1).split(',')
            for key in citation_keys:
                key = key.strip()
                if key not in citations:
                    citations[key] = True
                    
        return citations

    def extract_figures(self, content):
        """Extract figures and captions."""
        figure_pattern = r'\\begin{figure}(.*?)\\end{figure}'
        caption_pattern = r'\\caption{(.*?)}'
        
        figures = []
        
        figure_matches = re.finditer(figure_pattern, content, re.DOTALL)
        for i, match in enumerate(figure_matches):
            figure_content = match.group(1)
            caption_match = re.search(caption_pattern, figure_content, re.DOTALL)
            
            if caption_match:
                caption = caption_match.group(1)
                # Clean the caption
                caption = re.sub(r'\\label{.*?}', '', caption)
                caption = LatexNodes2Text().latex_to_text(caption)
                figures.append({
                    'id': f"fig{i+1}",
                    'caption': caption.strip()
                })
                
        return figures

    def extract_tables(self, content):
        """Extract tables and captions."""
        table_pattern = r'\\begin{table}(.*?)\\end{table}'
        caption_pattern = r'\\caption{(.*?)}'
        
        tables = []
        
        table_matches = re.finditer(table_pattern, content, re.DOTALL)
        for i, match in enumerate(table_matches):
            table_content = match.group(1)
            caption_match = re.search(caption_pattern, table_content, re.DOTALL)
            
            if caption_match:
                caption = caption_match.group(1)
                # Clean the caption
                caption = re.sub(r'\\label{.*?}', '', caption)
                caption = LatexNodes2Text().latex_to_text(caption)
                tables.append({
                    'id': f"tab{i+1}",
                    'caption': caption.strip()
                })
                
        return tables

    def extract_sections(self, content):
        """Extract document structure (sections, subsections)."""
        section_patterns = [
            (r'\\section{(.*?)}', 1),
            (r'\\subsection{(.*?)}', 2),
            (r'\\subsubsection{(.*?)}', 3)
        ]
        
        sections = []
        
        for pattern, level in section_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                title = match.group(1)
                # Clean the title
                title = LatexNodes2Text().latex_to_text(title)
                sections.append({
                    'level': level,
                    'title': title.strip()
                })
                
        # Sort sections by their position in the document
        sections.sort(key=lambda x: content.find(x['title']))
        
        return sections

    def process_math(self, content):
        """Preserve mathematical formulas with original LaTeX notation."""
        # First, preserve LaTeX math environments by converting them to markdown math blocks
        display_math_patterns = [
            (r'\$([^$]+?)\$', r'$\1$'),
            (r'\\begin{equation}(.*?)\\end{equation}', r'$$\n\1\n$$'),
            (r'\\begin{eqnarray}(.*?)\\end{eqnarray}', r'$$\n\1\n$$'),
            (r'\\begin{align}(.*?)\\end{align}', r'$$\n\1\n$$'),
            (r'\\begin{multline}(.*?)\\end{multline}', r'$$\n\1\n$$'),
            (r'\\begin{gather}(.*?)\\end{gather}', r'$$\n\1\n$$'),
            (r'\\begin{alignat}(.*?)\\end{alignat}', r'$$\n\1\n$$')
        ]
        
        for pattern, replacement in display_math_patterns:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
        return content

    def format_section_headers(self, content):
        """Format section headers using markdown."""
        # Find headers from our section structure and format them
        for section in self.section_structure:
            level = section['level']
            title = section['title']
            
            # Create markdown header with correct number of '#'
            markdown_header = '#' * (level+1) + ' ' + title
            
            # Pattern to find the title (with possible formatting) in the content
            title_pattern = re.escape(title)
            content = re.sub(r'[§]+[§\.]*\s*' + title_pattern + r'\s*(?:\n|$)', f"{markdown_header}\n", content, flags=re.IGNORECASE)
            
        # Clean up any leftover section symbols introduced by LatexNodes2Text
        content = re.sub(r'[§]+[§\.]*\s*(\w)', r'\1', content)
        return content

    def process_title(self, content):
        """Replace \title{} commands."""
        content = re.sub(r'\\title{(.*?)}', r'# \1', content)
        content = re.sub(r'\\maketitle', '', content)
        return content

    def clean_latex_commands(self, content):
        """Remove LaTeX-specific commands while preserving structure."""
        # Replace \date{} commands
        content = self.process_title(content)

        # Extract and save math blocks ($$\n...\n$$) to protect from conversion
        math_blocks = []

        def save_math_block(match):
            block_id = f"__MATH_BLOCK_{len(math_blocks)}__"
            math_blocks.append(match.group(0))  # Save the entire math block
            return block_id

        # Find and replace all math blocks with placeholders
        content = re.sub(r'\$\$\n.*?\n\$\$', save_math_block, content, flags=re.DOTALL)
        content = re.sub(r'\$.*?\$', save_math_block, content, flags=re.DOTALL)

        # Handle \% to be replaced with % (before removing comments)
        content = re.sub(r'\\%', '%', content)

        # Remove comments (but not the escaped % we just fixed)
        content = re.sub(r'(?<!\\)%.*?\n', '\n', content)

        # Replace \cite commands with citation markers
        def replace_cite(match):
            keys = match.group(1).split(',')
            formatted_keys = []
            for key in keys:
                key = key.strip()
                if key in self.citations:
                    citation_data = self.citations.get(key, {})
                    authors = citation_data.get('authors', 'Unknown Author')
                    title = citation_data.get('title', 'Unknown Title')
                    year = citation_data.get('year', '')

                    # Format author names for readability
                    authors = authors.replace(' and ', ', ')

                    formatted_keys.append(f"[{authors}, \"{title}\", {year}]")
                else:
                    formatted_keys.append(f"[{key}]")

            return ' '.join(formatted_keys)

        content = re.sub(r'\\cite(?:\[.*?\])?{([^}]*)}', replace_cite, content)

        # Replace figure references
        def replace_figure_ref(match):
            label = match.group(1)
            for fig in self.figures:
                if label == fig['id']:
                    return f"(Figure: {fig['caption']})"
            return f"(Figure {label})"

        content = re.sub(r'\\ref{(fig[^}]*)}', replace_figure_ref, content)

        # Replace table references
        def replace_table_ref(match):
            label = match.group(1)
            for tab in self.tables:
                if label == tab['id']:
                    return f"(Table: {tab['caption']})"
            return f"(Table {label})"

        content = re.sub(r'\\ref{(tab[^}]*)}', replace_table_ref, content)

        # Use pylatexenc for converting the rest of LaTeX to text
        converter = LatexNodes2Text()
        content = converter.latex_to_text(content)

        # Restore the math blocks
        for i, block in enumerate(math_blocks):
            block_id = f"__MATH_BLOCK_{i}__"
            content = content.replace(block_id, block)

        return content

    def remove_indentation(self, content):
        """Remove indentation from text."""
        lines = content.split('\n')
        unindented_lines = [line.strip() for line in lines]
        return '\n'.join(unindented_lines)
        
    def remove_multiple_blank_lines(self, content):
        """Remove multiple consecutive blank lines."""
        # Replace multiple blank lines with a single blank line
        return re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

    def process_file_src(self, reference):
        """Process a single LaTeX paper."""
        reference_dir = self.source_dir / reference
        
        if not reference_dir.exists():
            print(f"Directory not found: {reference_dir}")
            return False
        
        # Find main tex file
        main_tex_file = self.find_main_tex_file(reference_dir)
        if not main_tex_file:
            print(f"No .tex file found in {reference_dir}")
            return False
        
        print(f"Processing {reference}: {main_tex_file}")
        
        # Read the content of the main tex file
        with open(main_tex_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract citation keys
        citation_keys = self.extract_citations(content)
        
        # Extract bibliography entries
        bib_entries = self.extract_bib_entries(reference_dir)
        
        # Store citations for use in cleaning
        self.citations = {key: bib_entries.get(key, {}) for key in citation_keys}
        
        # Extract figures with captions
        self.figures = self.extract_figures(content)
        
        # Extract tables with captions
        self.tables = self.extract_tables(content)
        
        # Extract document structure
        self.section_structure = self.extract_sections(content)
        
        # Process mathematical formulas
        content = self.process_math(content)
        
        # Clean LaTeX commands and format text
        cleaned_content = self.clean_latex_commands(content)
        
        # Format section headers using markdown
        formatted_content = self.format_section_headers(cleaned_content)
        
        # Remove indentation
        unindented_content = self.remove_indentation(formatted_content)
        
        # Remove multiple blank lines
        final_content = self.remove_multiple_blank_lines(unindented_content)
        
        # Create output directory
        output_dir = self.output_dir / reference
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the processed text as markdown (.md) file
        processed_file = output_dir / "processed_text.md"
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # Save metadata (structure, figures, tables, citations)
        metadata = {
            'structure': self.section_structure,
            'figures': self.figures,
            'tables': self.tables,
            'citations': self.citations
        }
        
        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Processed {reference}: Output saved to {output_dir}")
        return True

    def process_file_pdf(self, reference):
        markdown_content = ""
        with pdfplumber.open(f"downloads/{reference}.pdf") as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                markdown_content += text + "\n\n"

        # Create output directory
        output_dir = self.output_dir / reference
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the processed text as markdown (.md) file
        processed_file = output_dir / "processed_text.md"
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Processed {reference}: Output saved to {output_dir}")
        return True

    def process_all(self):
        """Process all papers in the sources directory."""
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Get all reference directories
        references = [d.name for d in self.source_dir.iterdir() if d.is_dir()]
        total = len(references)
        processed = 0
        failed = 0
        
        print(f"Found {total} papers to process")
        
        for i, reference in enumerate(references):
            print(f"\nProcessing paper {i+1}/{total}: {reference}")
            try:
                success = self.process_file_src(reference)
                if success:
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"Error processing {reference}: {str(e)}")
                failed += 1
        
        print(f"\n--- Summary ---")
        print(f"Total papers: {total}")
        print(f"Successfully processed: {processed}")
        print(f"Failed: {failed}")
        print("Done!")
        

def main():
    # Define paths
    base_dir = Path(__file__).parent
    source_dir = base_dir / "sources"
    output_dir = base_dir / "outputs"
    
    # Delete existing outputs directory if it exists
    if os.path.exists(output_dir):
        print(f"Removing existing outputs directory: {output_dir}")
        import shutil
        shutil.rmtree(output_dir)
    
    print("Starting LaTeX processing for LLM fine-tuning...")
    
    processor = LatexProcessor(source_dir, output_dir)
    processor.process_all()
    

if __name__ == "__main__":
    main()