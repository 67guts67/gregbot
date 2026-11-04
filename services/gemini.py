import os
import google.genai as genai
from pathlib import Path

SYSTEMPROMPT = Path("./gregbot_system.txt").read_text(encoding="utf-8")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def ask_gemini(prompt, images=None):
    """images: list of (base64_str, mime_type) tuples"""
    content = [{"type": "text", "text": prompt}]

    for data, mime in images or []:
        content.append({"type": "image", "data": data, "mime_type": mime})

    response = client.interactions.create(
        model="gemini-3.1-flash-lite",
        system_instruction=SYSTEMPROMPT,
        input=content
    )

    return response.output_text