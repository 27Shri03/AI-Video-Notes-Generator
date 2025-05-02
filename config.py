import os
from dotenv import load_dotenv

load_dotenv()

WORD_LIMIT = int(os.getenv("WORD_LIMIT", 4000))
HF_TOKEN = os.getenv("HF_TOKEN")  # New addition

