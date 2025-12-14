# Scientific Paper LLM Fine-Tuning Project

## [Project Slides](https://docs.google.com/presentation/d/1W_tYOJ63GjW5nJbiKRP8uSWlRA14w2iVbykZ6S5aOE4/edit?usp=sharing)

## Goal
The goal of this project is to fine-tune the Meta Llama 3.1-8B model on a dataset of scientific papers (specifically in Quantum Computing and Superconducting Qubits) relevant for the work developed at TII's Quantum Computing Lab. The objective is to optimize the LLM to explain complex scientific and mathematical concepts found in these papers.

## Project Structure & Workflow

The project follows a sequential workflow from data acquisition to model benchmarking.

### Step 1: Data Acquisition
**Script**: `01_download_and_extract.py`
-   Reads reference numbers from `references.csv`.
-   Downloads source code (LaTeX) for each paper from `arxiv.org`.
-   Extracted contents are saved to `sources/{REFERENCE_NUMBER}`.

### Step 2: Data Processing
**Script**: `02_process_latex.py`
-   Parses the raw LaTeX files to extract clean text.
-   Preserves mathematical formulas (LaTeX syntax).
-   Handles citations and document structure (sections, subsections).
-   Outputs Markdown-formatted text to `outputs/{REFERENCE_NUMBER}`.

### Step 3: Dataset Preparation
**Script**: `03_prepare_dataset.py`
-   Converts the processed Markdown files into a structured dataset for training.
-   Generates JSONL files:
    -   `dataset/train.jsonl` & `dataset/train_enhanced.jsonl`
    -   `dataset/validation.jsonl` & `dataset/validation_enhanced.jsonl`
-   Each entry contains a "prompt" (question) and "completion" (answer derived from the paper).

### Step 4: Fine-Tuning
**Script**: `04_fine_tuning.py`
-   **Model**: Meta Llama 3.1-8B (Unsloth optimized).
-   **Method**: LoRA (Low-Rank Adaptation) parameter-efficient fine-tuning.
-   **Configuration**:
    -   Rank: 32, Alpha: 16
    -   Target Modules: q_proj, k_proj, v_proj, o_proj, etc.
    -   Precision: 4-bit quantization.
-   **Output**: Fine-tuned adapter saved in `lora_model`.

### Step 5: Inference
**Script**: `05_inference.py`
-   demonstrates how to load the fine-tuned model and generate a response for a single prompt.
-   Uses the Chat Template format: `<|system|>...<|user|>...<|assistant|>...`.

### Step 6: Benchmarking & Comparison
**Script**: `06_benchmark_models.py`

-   Loads both the **Base Model** (Llama 3.1-8B) and the **Fine-Tuned Model**.
-   Generates responses for 10 specific scientific questions.
-   Saves a side-by-side comparison to `model_comparison.md` to validate the quality improvements.

## Environment Setup

### Prerequisites
-   Windows OS (Project developed on Windows 11).
-   NVIDIA GPU with CUDA support (e.g., RTX 4090).
-   Visual Studio with C++ build tools.
-   CUDA Toolkit.

### Installation
Refer to `Unsloth Installation Windows.md` for detailed environment setup.
1.  Install NVIDIA drivers.
2.  Install PyTorch with CUDA support.
3.  Install `unsloth`, `xformers`, and other dependencies from `requirements_finetuning.txt`.

## Usage Summary

To reproduce the entire pipeline:

1.  **Download Data**:
    ```bash
    python 01_download_and_extract.py
    ```
2.  **Process Text**:
    ```bash
    python 02_process_latex.py
    ```
3.  **Create Dataset**:
    ```bash
    python 03_prepare_dataset.py
    ```
4.  **Train Model**:
    ```bash
    python 04_fine_tuning.py
    ```
5.  **Benchmark**:
    ```bash
    python 06_benchmark_models.py
    ```
