#!/usr/bin/env python
import os
import json
import random
from pathlib import Path
import re

class DatasetPreparer:
    """Prepare processed papers for llama3 fine-tuning."""
    
    def __init__(self, outputs_dir, dataset_dir):
        """Initialize the dataset preparer."""
        self.outputs_dir = Path(outputs_dir)
        self.dataset_dir = Path(dataset_dir)
        self.papers = []
        
    def load_processed_papers(self):
        """Load all processed papers from the outputs directory."""
        paper_count = 0
        
        # Get all reference directories in the outputs folder
        for paper_dir in self.outputs_dir.iterdir():
            if paper_dir.is_dir():
                paper_id = paper_dir.name
                md_file = paper_dir / "processed_text.md"
                metadata_file = paper_dir / "metadata.json"
                
                if md_file.exists() and metadata_file.exists():
                    # Load the processed text
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Load the metadata
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Store the paper data
                    self.papers.append({
                        'paper_id': paper_id,
                        'content': content,
                        'metadata': metadata
                    })
                    paper_count += 1
        
        print(f"Loaded {paper_count} processed papers")
        return paper_count
    
    def format_for_llama3(self, paper):
        """Format a paper for llama3 fine-tuning."""
        content = paper['content']
        metadata = paper['metadata']
        paper_id = paper['paper_id']
        
        # Extract title from the content (assuming it starts with # for Markdown h1)
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Paper {paper_id}"
        
        # Create a prompt that asks for information about the paper
        prompts = [
            f"Please summarize the paper titled '{title}'.",
            f"What are the main findings of the paper '{title}'?",
            f"Explain the methodology used in the paper '{title}'.",
            f"What mathematical concepts are used in the paper '{title}'?",
            f"What are the key contributions of the paper '{title}'?"
        ]
        
        # Select a random prompt for this paper
        prompt = random.choice(prompts)
        
        # Format for llama3 fine-tuning
        formatted_example = {
            "prompt": prompt,
            "completion": content
        }
        
        return formatted_example
    
    def create_training_examples(self):
        """Create training examples from all papers."""
        training_examples = []
        
        for paper in self.papers:
            example = self.format_for_llama3(paper)
            training_examples.append(example)
            
        return training_examples
    
    def split_dataset(self, examples, train_ratio=0.8):
        """Split the dataset into training and validation sets."""
        # Shuffle the examples
        random.shuffle(examples)
        
        # Calculate split index
        split_idx = int(len(examples) * train_ratio)
        
        # Split the dataset
        train_examples = examples[:split_idx]
        val_examples = examples[split_idx:]
        
        return train_examples, val_examples
    
    def prepare_dataset(self):
        """Prepare the complete dataset for llama3 fine-tuning."""
        # Create dataset directory if it doesn't exist
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        # Load all processed papers
        self.load_processed_papers()
        
        if not self.papers:
            print("No processed papers found. Run process_latex.py first.")
            return False
        
        # Create training examples
        all_examples = self.create_training_examples()
        
        # Split into training and validation sets
        train_examples, val_examples = self.split_dataset(all_examples)
        
        # Create llama3 compatible JSONL files
        train_path = self.dataset_dir / "train.jsonl"
        val_path = self.dataset_dir / "validation.jsonl"
        
        # Save training examples
        with open(train_path, 'w', encoding='utf-8') as f:
            for example in train_examples:
                f.write(json.dumps(example) + '\n')
        
        # Save validation examples
        with open(val_path, 'w', encoding='utf-8') as f:
            for example in val_examples:
                f.write(json.dumps(example) + '\n')
        
        # Save dataset information
        info = {
            "total_examples": len(all_examples),
            "train_examples": len(train_examples),
            "validation_examples": len(val_examples),
            "papers_used": [p['paper_id'] for p in self.papers]
        }
        
        with open(self.dataset_dir / "dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)
        
        print(f"Dataset prepared successfully:")
        print(f"  - Total examples: {len(all_examples)}")
        print(f"  - Training examples: {len(train_examples)}")
        print(f"  - Validation examples: {len(val_examples)}")
        print(f"  - Output files: {train_path}, {val_path}")
        
        return True
    
    def create_enhanced_dataset(self):
        """Create an enhanced dataset with various types of training examples."""
        # Create dataset directory if it doesn't exist
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        # Load all processed papers
        self.load_processed_papers()
        
        if not self.papers:
            print("No processed papers found. Run process_latex.py first.")
            return False
        
        # Enhanced examples will contain different types of training data
        enhanced_examples = []
        
        for paper in self.papers:
            content = paper['content']
            metadata = paper['metadata']
            paper_id = paper['paper_id']
            
            # Extract title from the content (assuming it starts with # for Markdown h1)
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else f"Paper {paper_id}"
            
            # 1. Create a summarization example
            enhanced_examples.append({
                "prompt": f"Please summarize the paper titled '{title}'.",
                "completion": self.extract_summary(content)
            })
            
            # 2. Create a question answering example about methodology
            enhanced_examples.append({
                "prompt": f"What methodology was used in the paper '{title}'?",
                "completion": self.extract_methodology(content, metadata)
            })
            
            # 3. Create a mathematical concepts example
            enhanced_examples.append({
                "prompt": f"Explain the key mathematical concepts in '{title}'.",
                "completion": self.extract_math_concepts(content)
            })
            
            # 4. Create a section-specific example
            for section in self.extract_sections(content):
                enhanced_examples.append(section)
                
            # 5. Create a full paper example
            enhanced_examples.append({
                "prompt": f"Provide the full content of the paper '{title}'.",
                "completion": content
            })
            
        # Split into training and validation sets
        train_examples, val_examples = self.split_dataset(enhanced_examples)
        
        # Create llama3 compatible JSONL files
        train_path = self.dataset_dir / "train_enhanced.jsonl"
        val_path = self.dataset_dir / "validation_enhanced.jsonl"
        
        # Save training examples
        with open(train_path, 'w', encoding='utf-8') as f:
            for example in train_examples:
                f.write(json.dumps(example) + '\n')
        
        # Save validation examples
        with open(val_path, 'w', encoding='utf-8') as f:
            for example in val_examples:
                f.write(json.dumps(example) + '\n')
        
        # Save dataset information
        info = {
            "total_examples": len(enhanced_examples),
            "train_examples": len(train_examples),
            "validation_examples": len(val_examples),
            "papers_used": [p['paper_id'] for p in self.papers],
            "example_types": ["summary", "methodology", "math_concepts", "sections", "full_paper"]
        }
        
        with open(self.dataset_dir / "enhanced_dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)
        
        print(f"Enhanced dataset prepared successfully:")
        print(f"  - Total examples: {len(enhanced_examples)}")
        print(f"  - Training examples: {len(train_examples)}")
        print(f"  - Validation examples: {len(val_examples)}")
        print(f"  - Output files: {train_path}, {val_path}")
        
        return True
    
    def extract_summary(self, content):
        """Extract a summary from the paper content."""
        # Look for abstract section
        abstract_match = re.search(r'##\s*Abstract\s*\n(.*?)(?=##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            return abstract
        
        # If no abstract found, use the first few paragraphs
        paragraphs = content.split('\n\n')
        # Skip potential title
        start_idx = 1 if paragraphs[0].startswith('#') else 0
        summary = '\n\n'.join(paragraphs[start_idx:start_idx+3])
        return summary
    
    def extract_methodology(self, content, metadata):
        """Extract methodology information from the paper."""
        # Look for methodology or methods section
        methods_match = re.search(r'##\s*(Method(ology|s)?|Approach|Experiment(s|al setup)?)\s*\n(.*?)(?=##|\Z)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if methods_match:
            methods = methods_match.group(4).strip()
            return methods
        
        # If no methods section found, look for a section mentioning methodology
        for section in metadata.get('structure', []):
            if re.search(r'method|approach|experiment', section.get('title', ''), re.IGNORECASE):
                section_title = section.get('title')
                section_match = re.search(f'##\\s*{re.escape(section_title)}\\s*\\n(.*?)(?=##|\\Z)', 
                                         content, re.DOTALL)
                if section_match:
                    return section_match.group(1).strip()
        
        # If still not found, return a default response
        return "The methodology section could not be found in this paper."
    
    def extract_math_concepts(self, content):
        """Extract mathematical concepts from the paper."""
        # Find all math blocks
        math_blocks = re.findall(r'\$\$(.*?)\$\$|\$(.*?)\$', content, re.DOTALL)
        
        # Concatenate the first few math expressions (if any)
        if math_blocks:
            math_expressions = []
            for block in math_blocks[:5]:  # Take first 5 math blocks
                # Each match is a tuple with the two capturing groups
                expr = block[0] if block[0] else block[1]
                math_expressions.append(f"$${expr}$$" if block[0] else f"${expr}$")
            
            return "The paper uses the following mathematical concepts and equations:\n\n" + "\n\n".join(math_expressions)
        else:
            return "No explicit mathematical formulas were found in this paper."
    
    def extract_sections(self, content):
        """Extract sections to create section-specific examples."""
        examples = []
        
        # Find all level 2 sections (## Section)
        sections = re.findall(r'##\s*(.*?)\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
        
        for section_title, section_content in sections:
            if len(section_content.strip()) > 100:  # Only use sections with substantial content
                examples.append({
                    "prompt": f"Explain the '{section_title}' section of the paper.",
                    "completion": section_content.strip()
                })
        
        return examples

def main():
    # Define paths
    base_dir = Path(__file__).parent
    outputs_dir = base_dir / "outputs"
    dataset_dir = base_dir / "dataset"
    
    # Create dataset preparer
    preparer = DatasetPreparer(outputs_dir, dataset_dir)
    
    # Create a simple dataset
    print("Preparing basic dataset for llama3 fine-tuning...")
    preparer.prepare_dataset()
    
    # Create an enhanced dataset with various types of examples
    print("\nPreparing enhanced dataset for llama3 fine-tuning...")
    preparer.create_enhanced_dataset()
    
    print("\nDataset preparation complete. Files are ready for llama3 fine-tuning.")

if __name__ == "__main__":
    main()