import torch
import asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
import streamlit as st
from config import HF_TOKEN  # Changed to use config

# Load from secrets
MODEL_NAME = "Aasif21/collab-cot-trained"

# Initialize in async-friendly way
@st.cache_resource
def load_model():
    if not HF_TOKEN:
        raise ValueError("Hugging Face token not found in .env file")
    
    login(token=HF_TOKEN)
    tokenizer = AutoTokenizer.from_pretrained("Aasif21/collab-cot-trained")
    model = AutoModelForCausalLM.from_pretrained(
        "Aasif21/collab-cot-trained",
        torch_dtype=torch.float16,
        device_map="auto"
    )
    return tokenizer, model

prompt_template = """Below is an instruction that describes a task, paired with an input that provides further context.
Write a response that appropriately completes the request. 

### Instruction:
You are a Expert Educator with advanced knowledge in Academic Topics and Notes Generation.
Given Below is the Question which means the transcript of the lecture. Generate high quality notes for it with proper depth understanding with examples.
### Question:
{}
<think>
{}</think>
### Response:
"""

async def generate_notes(transcript: str) -> str:
    """Async wrapper for model inference"""
    tokenizer, model = load_model()
    
    # Ensure single line input
    processed_text = transcript.replace("\n", " ")
    
    # Format prompt
    prompt = prompt_template.format(processed_text, "")
    
    # Run inference in thread pool
    def _run_inference():
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=2000,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        return tokenizer.decode(output[0], skip_special_tokens=True)
    
    try:
        decoded_output = await asyncio.to_thread(_run_inference)
        final_output= decoded_output.split("### Response:")[-1].strip()
        print("Decoded Output:" , decoded_output)
        # print(final_output)
        return final_output
    except Exception as e:
        st.error(f"Model error: {str(e)}")
        return ""