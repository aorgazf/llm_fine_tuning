# test_unsloth_installation.py

import torch

def main():
    # 1. Basic import check
    try:
        from unsloth import FastLanguageModel
    except Exception as e:
        raise RuntimeError("Failed to import Unsloth") from e

    # 2. CUDA availability (expected for Unsloth usage)
    cuda_ok = torch.cuda.is_available()
    print(f"CUDA available: {cuda_ok}")
    if not cuda_ok:
        print("Warning: CUDA not available. Unsloth will not function as intended.")

    # 3. Load a small model via Unsloth
    model_name = "unsloth/llama-3-8b-bnb-4bit"
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=128,
        dtype=None,
        load_in_4bit=True,
    )

    # 4. Switch to inference mode (verifies Unsloth patching)
    FastLanguageModel.for_inference(model)

    # 5. Run a trivial forward pass
    inputs = tokenizer(
        "Unsloth installation test.",
        return_tensors="pt"
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    print("Forward pass successful.")
    print(f"Logits shape: {outputs.logits.shape}")

if __name__ == "__main__":
    main()
