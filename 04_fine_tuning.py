from pathlib import Path
from datasets import load_dataset
from unsloth import FastLanguageModel
# import os
# import json
# import torch
# from transformers import TrainingArguments
# from trl import SFTConfig, SFTTrainer

MODEL_NAME = "unsloth/Meta-Llama-3.1-8B"
# MODEL_NAME = "meta-llama/Llama-3.1-8B"
DATASET_DIR = Path("dataset")
TRAIN_FILE = DATASET_DIR / "train_enhanced.jsonl"
VALIDATION_FILE = DATASET_DIR / "validation_enhanced.jsonl"

max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Meta-Llama-3.1-8B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
    # token = HF_TOKEN,
)

model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Supports any, but = 0 is optimized
    bias = "none",    # Supports any, but = "none" is optimized
    use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
    random_state = 3407,
    use_rslora = False,  # We support rank stabilized LoRA
    loftq_config = None, # And LoftQ
)


# Load dataset
print("Loading dataset...")
train_dataset = load_dataset("json", data_files=str(TRAIN_FILE), split="train")
validation_dataset = load_dataset("json", data_files=str(VALIDATION_FILE), split="train")

print(f"Train examples: {len(train_dataset)}")
print(f"Validation examples: {len(validation_dataset)}")

# Format dataset for training - making sure it works with our version of SFTTrainer
EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
formatted_text = """<|system|>\nYou are an expert scientific assistant who helps explain complex mathematics and physics concepts from research papers.\n<|user|>\n{}\n<|assistant|>\n{}"""
def formatting_prompts_func(examples):
    prompts = examples["prompt"]
    completions = examples["completion"]
    
    # Format for training directly with input/target separation instead of using dataset_text_field
    # Using Llama 3.1 chat template formatting

    texts = []
    for prompt, completion in zip(prompts, completions):
        # Must add EOS_TOKEN, otherwise your generation will go on forever!
        text = formatted_text.format(prompt, completion) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }

print("Formatting training dataset...")
train_dataset = train_dataset.map(formatting_prompts_func, batched=True)
print("Formatting validation dataset...")
validation_dataset = validation_dataset.map(formatting_prompts_func, batched=True)


from trl import SFTConfig, SFTTrainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = train_dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    packing = False, # Can make training 5x faster for short sequences.
    args = SFTConfig(
        dataset_num_proc=1,
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        # num_train_epochs = 1, # Set this for 1 full training run.
        max_steps = 60,
        learning_rate = 2e-4,
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none", # Use this for WandB etc
    ),
)

trainer_stats = trainer.train()



FastLanguageModel.for_inference(model) # Enable native 2x faster inference
inputs = tokenizer(
[
    formatted_text.format(
        "Explain what a transmon is.", # prompt
        "", # output - leave this blank for generation!
    )
], return_tensors = "pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens = 64, use_cache = True)
response = tokenizer.batch_decode(outputs)
print("Generated response:", response)
model.save_pretrained("lora_model")  # Local saving
tokenizer.save_pretrained("lora_model")









