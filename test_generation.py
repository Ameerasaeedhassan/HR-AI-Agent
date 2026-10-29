from pathlib import Path

from dotenv import dotenv_values
from google import genai
from google.genai import types


ENV_PATH = Path(__file__).resolve().parent / ".env"
config = dotenv_values(ENV_PATH, encoding="utf-8-sig")

api_key = config.get("GEMINI_API_KEY")

print("File exists:", ENV_PATH.is_file())
print("Key found:", bool(api_key))

if not api_key:
    raise ValueError(
        "Save GEMINI_API_KEY in the .env file beside this script."
    )

with genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=30_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
) as client:
    response = client.interactions.create(
        model="gemini-3.8-flash",
        input="Explain RAG in one short sentence for a beginner.",
    )

    print("\nResponse:")
    print(response.output_text)