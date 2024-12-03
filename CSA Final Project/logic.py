import re
from tkinter import Tk, Label, Button, filedialog, Text, Scrollbar, Canvas, Frame
from tkinter.messagebox import showerror
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
    clutter_keywords = [
        "store", "total", "due", "debit", "credit", "cash", "payment",
        "change", "balance", "date", "time", "vat", "tax", "thank you",
        "subtotal", "discount", "offer", "feedback", "survey", "prices",
        "network", "terminal", "ref", "aid", "appr code", "st#", "op#", "te#", "tr#", "tc#"
    ]
    if any(keyword in text.lower() for keyword in clutter_keywords):
        return False

    # Ignore lines with excessive numbers or symbols
    if len(re.findall(r'\d', text)) > len(text) * 0.6 or re.search(r'[^\w\s.,]', text):
        return False

    # Ignore lines that are too short or too long
    if len(text) < 5 or len(text) > 50:
        return False

    # Accept lines with price patterns only if they include item-like text
    if re.search(r'\d+(\.\d{2})?\s*[€$]', text):
        return True if any(c.isalpha() for c in text) else False

    # Passed all filters, consider it an item line
    return True


# Clean and deduplicate extracted items
def clean_extracted_items(items):
    return sorted(set(item.strip().capitalize() for item in items if item.strip()))

# Process the receipt image
def process_receipt(image_path):
    try:
        model = ocr_predictor(pretrained=True)
        receipt = DocumentFile.from_images(image_path)
        result = model(receipt)
        extracted_text = result.export()['pages'][0]['blocks']

        raw_items = []
        for block in extracted_text:
            for line in block['lines']:
                text = ' '.join(word['value'] for word in line['words'])
                if is_item_line(text):
                    raw_items.append(text.strip())

        return clean_extracted_items(raw_items)

    except FileNotFoundError:
        showerror("Error", f"File '{image_path}' not found.")
        return []
    except Exception as e:
        showerror("Error", f"Error processing receipt: {e}")
        return []

# Calculate Pfand
def calculate_pfand(items):
    bottle_keywords = [
        "coca cola", "pepsi", "dasani", "bottle", "sprite", "fanta",
        "evian", "volvic", "nestle", "mineral water", "glass bottle", "plastic bottle"
    ]
    bottle_count = sum(1 for item in items if any(keyword in item.lower() for keyword in bottle_keywords))
    pfand_per_bottle = 0.25
    return round(bottle_count * pfand_per_bottle, 2)

# Tkinter GUI
class ReceiptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pfand System")

        # Header Label
        Label(root, text="Pfand System", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Buttons
        Button(root, text="Load Receipt Image", command=self.load_receipt, width=20).pack(pady=5)
        Button(root, text="Exit", command=root.quit, width=20).pack(pady=5)

        # Results Frame
        self.results_frame = Frame(root)
        self.results_frame.pack(pady=10)

        # Scrollable Text Widget for Results
        canvas = Canvas(self.results_frame)
        scrollbar = Scrollbar(self.results_frame, orient="vertical", command=canvas.yview)
        self.results_text_frame = Frame(canvas)
        self.results_text_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.results_text_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.results_text = Text(self.results_text_frame, width=60, height=20, wrap="word", state="disabled")
        self.results_text.pack()

    def load_receipt(self):
        file_path = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
        )
        if not file_path:
            return

        self.process_and_display(file_path)

    def process_and_display(self, file_path):
        # Clear previous results
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")

        # Process receipt
        items = process_receipt(file_path)

        if items:
            self.results_text.insert("end", "Extracted Items:\n")
            self.results_text.insert("end", "\n".join(items) + "\n")

            # Calculate Pfand
            pfand = calculate_pfand(items)
            self.results_text.insert("end", f"\nTotal Pfand Refund: €{pfand}\n")
        else:
            self.results_text.insert("end", "No valid items found or error in processing.")

        # Disable text editing
        self.results_text.config(state="disabled")

# Main function
if __name__ == '__main__':
    root = Tk()
    app = ReceiptApp(root)
    root.mainloop()
