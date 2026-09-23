import os
import time
from dotenv import load_dotenv
from google import genai
load_dotenv()

client = genai.Client(api_key= os.getenv("GEMINI_API_KEY"))

def generate_answer(question: str) -> dict:
    start_time = time.perf_counter()
    response = client.models.generate_content(model="gemini-3.6-flash", contents=question)
    latency = time.perf_counter() - start_time
    return {"answer": response.text, 
    "latency": latency, 
    "input_tokens": response.usage_metadata.prompt_token_count,
    "output_tokens": response.usage_metadata.candidates_token_count,
    "thought_tokens": response.usage_metadata.thoughts_token_count,
    "total_tokens": response.usage_metadata.total_token_count}