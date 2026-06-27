import os
import json
from dotenv import load_dotenv
import anthropic
from invoice_processor.server import read_invoice, save_to_csv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

EXTRACT_PROMPT = """You are an invoice data extractor.
Extract the following fields from this invoice and return ONLY a valid JSON object with these keys:
- vendor (company/person who issued the invoice)
- date (invoice date in YYYY-MM-DD format)
- invoice_number
- total (numeric value only, no currency symbol)
- currency (e.g. USD, EUR, ILS)
- items (brief summary of line items as a single string)

If a field is not found, use an empty string. Return only the JSON, no explanation."""


def process_invoice(file_path: str) -> dict:
    """Send invoice to Claude and extract structured data."""
    invoice = read_invoice(file_path)

    if "error" in invoice:
        print(f"Error reading file: {invoice['error']}")
        return invoice

    if invoice["type"] == "text":
        messages = [{"role": "user", "content": f"{EXTRACT_PROMPT}\n\nInvoice text:\n{invoice['content']}"}]
    else:
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": invoice["media_type"],
                        "data": invoice["content"],
                    },
                },
                {"type": "text", "text": EXTRACT_PROMPT}
            ]
        }]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=messages,
    )

    raw = response.content[0].text.strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        print(f"Could not parse Claude response:\n{raw}")
        return {"error": "Invalid JSON from Claude", "raw": raw}

    extracted["file"] = invoice["file"]
    result = save_to_csv(extracted)
    print(f"Extracted: {extracted}")
    print(result)
    return extracted
