import os
import csv
import requests
import tarfile
import shutil
from pathlib import Path
import time

def read_references(file_path):
    """Read reference numbers from a CSV file."""
    references = []
    with open(file_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles the BOM character
        reader = csv.reader(file)
        for row in reader:
            # Each row might contain just one element
            if row and row[0].strip():
                references.append(row[0].strip())
    return references

def create_directory(dir_path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

def download_paper_src(reference, download_dir):
    """Download a paper from arxiv.org."""
    url = f"https://arxiv.org/src/{reference}"
    file_path = os.path.join(download_dir, f"{reference}.tar.gz")
    
    # Skip if already downloaded
    if os.path.exists(file_path):
        print(f"File already exists: {file_path}")
        return file_path
    
    print(f"Downloading {reference} from {url}...")
    try:
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {file_path}")
            return file_path
        else:
            print(f"Failed to download {reference}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {reference}: {str(e)}")
        return None
    
def download_paper_pdf(reference, download_dir):
    """Download a paper from arxiv.org."""
    url = f"https://arxiv.org/pdf/{reference}"
    file_path = os.path.join(download_dir, f"{reference}.pdf")
    
    # Skip if already downloaded
    if os.path.exists(file_path):
        print(f"File already exists: {file_path}")
        return file_path
    
    print(f"Downloading {reference} from {url}...")
    try:
        response = requests.get(url, stream=True)
        
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {file_path}")
            return file_path
        else:
            print(f"Failed to download {reference}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {reference}: {str(e)}")
        return None

def extract_archive(archive_path, extract_dir):
    """Extract a tar.gz archive to the specified directory."""
    if not os.path.exists(archive_path):
        print(f"Archive file not found: {archive_path}")
        return False
    
    create_directory(extract_dir)
    
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
        print(f"Extracted {archive_path} to {extract_dir}")
        return True
    except Exception as e:
        print(f"Error extracting {archive_path}: {e}")
        return False

def main():
    # Define paths
    base_dir = Path(__file__).parent
    references_file = base_dir / "references.csv"
    downloads_dir = base_dir / "downloads"
    sources_dir = base_dir / "sources"
    
    # Create downloads directory if it doesn't exist
    create_directory(downloads_dir)
    
    # Create sources directory if it doesn't exist
    create_directory(sources_dir)
    
    # Read reference numbers
    references = read_references(references_file)
    print(f"Found {len(references)} references")
    
    # Count to track progress
    processed = 0
    successful = 0
    
    # Process each reference
    for i, reference in enumerate(references):
        print(f"\nProcessing reference {i+1}/{len(references)}: {reference}")
        
        # Step 1: Download paper src and pdf
        pdf_path = download_paper_pdf(reference, downloads_dir)
        archive_path = download_paper_src(reference, downloads_dir)
        processed += 1
        
        if archive_path:
            # Step 2: Extract archive
            extract_dir = sources_dir / reference
            if extract_archive(archive_path, extract_dir):
                successful += 1
            
        # Add a small delay to avoid overwhelming the server
        time.sleep(1)
    
    print(f"\n--- Summary ---")
    print(f"Total references: {len(references)}")
    print(f"Processed: {processed}")
    print(f"Successfully extracted: {successful}")
    print("Done!")

if __name__ == "__main__":
    main()