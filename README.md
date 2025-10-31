# PDF Multi-Tool Editor

A feature-rich, locally hosted Flask web application for editing, converting, and securing PDF files with a modern and responsive interface.

## Features

- **Organize PDFs:**
  - Merge, split, extract, rotate, remove, and reorder pages.
  
- **Convert to PDF:**
  - Images to PDF, HTML to PDF, Markdown to PDF.

- **Convert from PDF:**
  - PDF to Images, Text, HTML, CSV (extract tables).

- **Sign & Security:**
  - Add/remove password protection, add watermark.

- **View & Edit:**
  - Add images, page numbers, display metadata, compress files.

- **Fully offline:** 
  - Works entirely on your local machine without the need for an internet connection.
  
- **Simple Drag-and-Drop Interface:**
  - Intuitive, user-friendly design.

## Screenshots

![Screenshot 1](https://github.com/user-attachments/assets/682da280-ad2b-4c6e-9378-741a9a5663f9)

---

![Screenshot 2](https://github.com/user-attachments/assets/ba9c8d34-95e0-4021-b7c0-3a022f96cc60)

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+**
- **pip** (for installing dependencies)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kunalrajbhar/PDF-Multi-Tool-Editor.git
   cd Pdf-Multi-Tool-Editor

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Poppler** (required for converting PDFs to images and other formats):

   * **Windows:** [Download poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) and add the `bin` folder to your system PATH.
   * **Mac:** Install via Homebrew:

     ```bash
     brew install poppler
     ```
   * **Linux:** Install via `apt`:

     ```bash
     sudo apt-get install poppler-utils
     ```

### Running the App

Once everything is installed, you can run the app with:

```bash
python app.py
```

After running this command, open your browser and go to [http://localhost:5000](http://localhost:5000) to start using the tool.

## Usage

1. Choose the tool you want to use (e.g., merge, split, convert, add watermark, etc.).
2. Upload your PDF files, images, or other content as per the selected tool.
3. Follow the on-screen instructions.
4. Download the resulting files directly from the interface.

## Folder Structure

```bash
pdf-multi-tool-editor/
├── app.py                # Main application file
├── requirements.txt      # List of dependencies
├── README.md             # Project documentation
├── uploads/              # Temporary folder for uploaded files
├── outputs/              # Folder where processed files are saved



## Dependencies

The following dependencies are required for the app to work:

* Flask
* PyPDF2
* Pillow
* reportlab
* pdfplumber
* img2pdf
* pdf2image
* markdown
* python-pptx
* weasyprint
* beautifulsoup4

*See `requirements.txt` for exact versions.*

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss the changes you would like to make. Ensure that your changes do not break the functionality of the application and that they are well-documented.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
