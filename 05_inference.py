max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True

# from unsloth import FastLanguageModel
# model, tokenizer = FastLanguageModel.from_pretrained(
#     model_name = "lora_model", # YOUR MODEL YOU USED FOR TRAINING
#     max_seq_length = max_seq_length,
#     dtype = dtype,
#     load_in_4bit = load_in_4bit,
# )
# FastLanguageModel.for_inference(model) # Enable native 2x faster inference

#############
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer
model = AutoPeftModelForCausalLM.from_pretrained(
    "lora_model", # YOUR MODEL YOU USED FOR TRAINING
    load_in_4bit = load_in_4bit,
)
tokenizer = AutoTokenizer.from_pretrained("lora_model")




EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
formatted_text = """<|system|>\nYou are an expert scientific assistant who helps explain complex mathematics and physics concepts from research papers.\n<|user|>\n{}\n<|assistant|>\n{}"""


inputs = tokenizer(
[
    formatted_text.format(
        "Explain how to do entanglement metrology with a single measurement channel.", # prompt
        "", # output - leave this blank for generation!
    )
], return_tensors = "pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens = 64, use_cache = True)
response = tokenizer.batch_decode(outputs)
print("Generated response:", response)

# from transformers import TextStreamer
# text_streamer = TextStreamer(tokenizer)
# _ = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 128)




