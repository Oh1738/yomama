import sys
from invoice_processor.processor import process_invoice


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m invoice_processor.main <invoice_file>")
        print("Example: python -m invoice_processor.main invoice.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Processing: {file_path}")
    result = process_invoice(file_path)

    if "error" in result:
        print(f"Failed: {result['error']}")
        sys.exit(1)
    else:
        print("\nDone! Data saved to invoices_output.csv")


if __name__ == "__main__":
    main()
