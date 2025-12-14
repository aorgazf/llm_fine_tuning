import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import AutoPeftModelForCausalLM
import gc

# 10 Questions based on the scientific articles
QUESTIONS = [
    "In microwave resonator measurements, the transmission response is often visualized as a circle in the complex plane. Explain what information about the resonator can be extracted from this circle in the ideal, symmetric case, and how internal and external quality factors are conceptually related to it.",
    "Non-ideal experimental conditions can produce asymmetric resonance line shapes. Describe two physical mechanisms that can lead to this asymmetry and explain how they modify the interpretation of the measured transmission response.",
    "Two analysis approaches for asymmetric resonance data are a rotation-based method and a diameter-corrected method. Explain why the rotation-based approach can systematically overestimate the internal quality factor at high asymmetry, and how the diameter-corrected approach avoids this issue.",
    "Why are superconducting microwave resonators useful components in low-temperature quantum experiments, and what role does their quality factor play in these applications?",
    "Explain how coupling a resonator to its environment modifies its observed resonance properties, and distinguish between internal and external contributions to loss.",
    "Discuss how measurement back-action and coupling strength trade off against each other in resonator-based experiments, particularly in the context of extracting reliable device parameters.",
    "What is meant by random quantum circuits, and why are they useful for benchmarking quantum processors?",
    "Explain the basic idea behind using output probability distributions to estimate the fidelity of a quantum processor running random circuits.",
    "Why does the effectiveness of random-circuit benchmarking rely on statistical concentration phenomena in high-dimensional Hilbert spaces, and what implications does this have for scalability?",
    "Describe the purpose of cross-entropy benchmarking in the characterization of multi-qubit quantum processors.",
]

SYSTEM_PROMPT = """You are an expert scientists with expertise in quantum computing with superconducting qubits who helps explain complex mathematics and physics concepts discussed in research papers. You are able to condense your responses into one-paragraphs."""

def format_prompt(question):
    return f"""<|system|>
{SYSTEM_PROMPT}
<|user|>
{question}
<|assistant|>
"""

def generate_responses(model_name, is_peft=False):
    print(f"Loading model: {model_name}")
    
    if is_peft:
        # Load Fine-Tuned Model
        model = AutoPeftModelForCausalLM.from_pretrained(
            model_name,
            load_in_4bit=True,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    else:
        # Load Base Model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            load_in_4bit=True,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    logger = []
    
    print("Starting generation...")
    for i, question in enumerate(QUESTIONS):
        print(f"Processing Q{i+1}/{len(QUESTIONS)}")
        prompt = format_prompt(question)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        
        outputs = model.generate(**inputs, max_new_tokens=256, use_cache=True)
        response_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        
        # Extract just the assistant's part if possible, though batch_decode returns full text usually
        # The cleaning depends on the exact model output format, but usually we get the prompt back.
        # We'll save the full raw text for now or split if clear.
        
        # Simple split to try and get only the answer
        try:
            answer = response_text.split("<|assistant|>\n")[-1].strip()
        except:
            answer = response_text

        logger.append({
            "question": question,
            "response": answer
        })

    # Cleanup
    del model
    del tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    
    return logger

def save_comparison(base_results, ft_results):
    with open("model_comparison.md", "w") as f:
        f.write("# Model Comparison: Base vs Fine-Tuned\n\n")
        f.write(f"**Base Model**: unsloth/meta-llama-3.1-8b-unsloth-bnb-4bit\n")
        f.write(f"**Fine-Tuned Model**: lora_model\n\n")
        
        for i, (base, ft) in enumerate(zip(base_results, ft_results)):
            f.write(f"## Question {i+1}\n")
            f.write(f"**Q: {base['question']}**\n\n")
            
            f.write("### Base Model Response\n")
            f.write(f"{base['response']}\n\n")
            
            f.write("### Fine-Tuned Model Response\n")
            f.write(f"{ft['response']}\n\n")
            f.write("---\n\n")

if __name__ == "__main__":
    base_model_name = "unsloth/meta-llama-3.1-8b-unsloth-bnb-4bit"
    ft_model_name = "lora_model"

    print("=== Benchmarking Base Model ===")
    base_results = generate_responses(base_model_name, is_peft=False)
    
    print("\n=== Benchmarking Fine-Tuned Model ===")
    ft_results = generate_responses(ft_model_name, is_peft=True)
    
    print("\nSaving results...")
    save_comparison(base_results, ft_results)
    print("Done! Results saved to model_comparison.md")
