import re
from doctr.models import ocr_predictor
from doctr.io import DocumentFile

# Check if a line is an item line
def is_item_line(text):
    """
    Determines if a line of text represents an item.

    Args:
        text (str): The text line to check.

    Returns:
        bool: True if the line is an item, False otherwise.
    """
    # Common non-item keywords to filter out
    clutter_keywords = [
        "store", "total", "due", "debit", "credit", "cash", "payment",
        "change", "balance", "date", "time", "vat", "tax", "thank you"
    ]
    if any(keyword in text.lower() for keyword in clutter_keywords):
        return False

    # Ignore lines with many digits (likely prices, totals, or dates)
    if len(re.findall(r'\d', text)) > 2:
        return False

    # Ignore very short or very long lines (unlikely to be items)
    if len(text) < 3 or len(text) > 50:
        return False

    # Ignore lines with special characters (non-item lines)
    if re.search(r'[!@#$%^&*()_+=|<>?{}~:;"]', text):
        return False

    # Passed all filters, consider it an item line
    return True

# Clean and deduplicate extracted items
def clean_extracted_items(items):
    """
    Post-process extracted items to remove duplicates and noise.

    Args:
        items (list): List of raw extracted items.

    Returns:
        list: Cleaned list of items.
    """
    cleaned_items = []
    seen_items = set()
    for item in items:
        item = item.strip().lower()  # Normalize case and whitespace
        if item not in seen_items:
            cleaned_items.append(item.capitalize())  # Format for readability
            seen_items.add(item)
    return cleaned_items

# Process the receipt image
def process_receipt(image_path):
    """
    Extracts cleaned item names from a receipt image.

    Args:
        image_path (str): Path to the receipt image.

    Returns:
        list: Cleaned list of extracted item names.
    """
    # Load pre-trained OCR model
    model = ocr_predictor(pretrained=True)

    # Load the receipt image
    receipt = DocumentFile.from_images(image_path)

    # Perform OCR and extract text
    result = model(receipt)
    extracted_text = result.export()['pages'][0]['blocks']

    raw_items = []
    for block in extracted_text:
        for idx, line in enumerate(block['lines']):
            text = ' '.join([word['value'] for word in line['words']])

            # Skip contextual clutter at the beginning or end of the receipt
            if idx < 3 or idx > len(block['lines']) - 3:
                continue

            # Check if the line is an item line
            if is_item_line(text):
                raw_items.append(text.strip())

    # Post-process items to clean duplicates and remove noise
    return clean_extracted_items(raw_items)

# Example usage
if __name__ == '__main__':
    # Path to the receipt image
    receipt_image = 'sample_2.png'

    # Process the receipt
    items = process_receipt(receipt_image)
    print("Extracted items:", items)
