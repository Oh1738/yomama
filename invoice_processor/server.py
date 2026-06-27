import fitz  # pymupdf
import base64
import csv
import os
from pathlib import Path


def read_invoice(file_path: str) -> dict:
    """Read a PDF or image invoice and return its content."""
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    if path.suffix.lower() == ".pdf":
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return {"type": "text", "content": text, "file": path.name}

    elif path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
        with open(file_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        ext = path.suffix.lower().strip(".")
        if ext == "jpg":
            ext = "jpeg"
        return {"type": "image", "content": image_data, "media_type": f"image/{ext}", "file": path.name}

    else:
        return {"error": f"Unsupported file type: {path.suffix}"}


def save_to_csv(data: dict, output_path: str = "invoices_output.csv") -> str:
    """Append extracted invoice data to a CSV file."""
    fieldnames = ["file", "vendor", "date", "invoice_number", "total", "currency", "items"]
    file_exists = os.path.exists(output_path)

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "file": data.get("file", ""),
            "vendor": data.get("vendor", ""),
            "date": data.get("date", ""),
            "invoice_number": data.get("invoice_number", ""),
            "total": data.get("total", ""),
            "currency": data.get("currency", ""),
            "items": data.get("items", ""),
        })

    return f"Saved to {output_path}"
