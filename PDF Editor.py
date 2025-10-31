# Save this as app.py

from flask import Flask, render_template, request, send_file, jsonify, session
from werkzeug.utils import secure_filename
import os
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PIL import Image
import io
import base64
from datetime import datetime
import uuid
import markdown
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import csv
from bs4 import BeautifulSoup
import img2pdf
import pdfplumber
from pdf2docx import Converter
import xml.etree.ElementTree as ET
from pptx import Presentation
from pptx.util import Inches
import tempfile
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Create necessary folders
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'html', 'md', 'csv', 'xml', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Multi-Tool Editor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 40px;
            font-size: 2.5em;
        }

        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .category {
            margin-bottom: 30px;
        }

        .category-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        .tool-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            color: white;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .tool-card h3 {
            margin-bottom: 8px;
            font-size: 1.2em;
        }

        .tool-card p {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            overflow-y: auto;
        }

        .modal-content {
            background: white;
            margin: 50px auto;
            padding: 40px;
            border-radius: 20px;
            max-width: 600px;
            position: relative;
        }

        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            font-size: 30px;
            cursor: pointer;
            color: #999;
        }

        .close:hover {
            color: #333;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }

        input[type="file"],
        input[type="text"],
        input[type="number"],
        input[type="password"],
        select,
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.3s;
            width: 100%;
            margin-top: 10px;
        }

        button:hover {
            transform: scale(1.05);
        }

        .success {
            background: #4caf50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }

        .error {
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }

        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .download-link {
            display: none;
            margin-top: 20px;
            text-align: center;
        }

        .download-link a {
            background: #4caf50;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            transition: transform 0.3s;
        }

        .download-link a:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 PDF Multi-Tool Editor</h1>

        <div class="category">
            <h2 class="category-title">Organize</h2>
            <div class="tools-grid">
                <div class="tool-card" onclick="openTool('merge')">
                    <h3>Merge PDFs</h3>
                    <p>Combine multiple PDFs into one</p>
                </div>
                <div class="tool-card" onclick="openTool('split')">
                    <h3>Split PDF</h3>
                    <p>Split PDF into separate pages</p>
                </div>
                <div class="tool-card" onclick="openTool('extract')">
                    <h3>Extract Pages</h3>
                    <p>Extract specific pages from PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('rotate')">
                    <h3>Rotate PDF</h3>
                    <p>Rotate PDF pages</p>
                </div>
                <div class="tool-card" onclick="openTool('remove')">
                    <h3>Remove Pages</h3>
                    <p>Delete specific pages from PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('organize')">
                    <h3>Organize Pages</h3>
                    <p>Reorder PDF pages</p>
                </div>
            </div>
        </div>

        <div class="category">
            <h2 class="category-title">Convert to PDF</h2>
            <div class="tools-grid">
                <div class="tool-card" onclick="openTool('image-to-pdf')">
                    <h3>Image to PDF</h3>
                    <p>Convert images to PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('html-to-pdf')">
                    <h3>HTML to PDF</h3>
                    <p>Convert HTML to PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('markdown-to-pdf')">
                    <h3>Markdown to PDF</h3>
                    <p>Convert Markdown to PDF</p>
                </div>
            </div>
        </div>

        <div class="category">
            <h2 class="category-title">Convert from PDF</h2>
            <div class="tools-grid">
                <div class="tool-card" onclick="openTool('pdf-to-image')">
                    <h3>PDF to Images</h3>
                    <p>Convert PDF pages to images</p>
                </div>
                <div class="tool-card" onclick="openTool('pdf-to-text')">
                    <h3>PDF to Text</h3>
                    <p>Extract text from PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('pdf-to-html')">
                    <h3>PDF to HTML</h3>
                    <p>Convert PDF to HTML</p>
                </div>
                <div class="tool-card" onclick="openTool('pdf-to-csv')">
                    <h3>PDF to CSV</h3>
                    <p>Extract tables to CSV</p>
                </div>
            </div>
        </div>

        <div class="category">
            <h2 class="category-title">Sign & Security</h2>
            <div class="tools-grid">
                <div class="tool-card" onclick="openTool('add-password')">
                    <h3>Add Password</h3>
                    <p>Protect PDF with password</p>
                </div>
                <div class="tool-card" onclick="openTool('remove-password')">
                    <h3>Remove Password</h3>
                    <p>Unlock protected PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('add-watermark')">
                    <h3>Add Watermark</h3>
                    <p>Add text watermark to PDF</p>
                </div>
            </div>
        </div>

        <div class="category">
            <h2 class="category-title">View & Edit</h2>
            <div class="tools-grid">
                <div class="tool-card" onclick="openTool('add-image')">
                    <h3>Add Image</h3>
                    <p>Insert images into PDF</p>
                </div>
                <div class="tool-card" onclick="openTool('add-page-numbers')">
                    <h3>Add Page Numbers</h3>
                    <p>Number PDF pages</p>
                </div>
                <div class="tool-card" onclick="openTool('get-info')">
                    <h3>Get PDF Info</h3>
                    <p>View PDF metadata</p>
                </div>
                <div class="tool-card" onclick="openTool('compress')">
                    <h3>Compress PDF</h3>
                    <p>Reduce PDF file size</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Generic Modal -->
    <div id="toolModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2 id="modalTitle">Tool Name</h2>
            <form id="toolForm" enctype="multipart/form-data">
                <div id="formFields"></div>
                <button type="submit">Process</button>
            </form>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Processing...</p>
            </div>
            <div class="success" id="success"></div>
            <div class="error" id="error"></div>
            <div class="download-link" id="downloadLink"></div>
        </div>
    </div>

    <script>
        let currentTool = '';

        const toolForms = {
            'merge': `
                <div class="form-group">
                    <label>Select PDF Files (Multiple)</label>
                    <input type="file" name="files" accept=".pdf" multiple required>
                </div>
            `,
            'split': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
            `,
            'extract': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Page Numbers (e.g., 1,3,5-7)</label>
                    <input type="text" name="pages" placeholder="1,3,5-7" required>
                </div>
            `,
            'rotate': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Rotation Angle</label>
                    <select name="angle" required>
                        <option value="90">90° Clockwise</option>
                        <option value="180">180°</option>
                        <option value="270">270° (90° Counter-clockwise)</option>
                    </select>
                </div>
            `,
            'remove': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Pages to Remove (e.g., 1,3,5)</label>
                    <input type="text" name="pages" placeholder="1,3,5" required>
                </div>
            `,
            'organize': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>New Page Order (e.g., 3,1,2,4)</label>
                    <input type="text" name="order" placeholder="3,1,2,4" required>
                </div>
            `,
            'image-to-pdf': `
                <div class="form-group">
                    <label>Select Image(s)</label>
                    <input type="file" name="files" accept="image/*" multiple required>
                </div>
            `,
            'html-to-pdf': `
                <div class="form-group">
                    <label>Select HTML File or Enter HTML</label>
                    <input type="file" name="file" accept=".html">
                </div>
                <div class="form-group">
                    <label>Or Enter HTML Code</label>
                    <textarea name="html" rows="10" placeholder="<html>...</html>"></textarea>
                </div>
            `,
            'markdown-to-pdf': `
                <div class="form-group">
                    <label>Select Markdown File or Enter Text</label>
                    <input type="file" name="file" accept=".md">
                </div>
                <div class="form-group">
                    <label>Or Enter Markdown</label>
                    <textarea name="markdown" rows="10" placeholder="# Heading..."></textarea>
                </div>
            `,
            'pdf-to-image': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Image Format</label>
                    <select name="format">
                        <option value="png">PNG</option>
                        <option value="jpg">JPG</option>
                    </select>
                </div>
            `,
            'pdf-to-text': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
            `,
            'pdf-to-html': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
            `,
            'pdf-to-csv': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
            `,
            'add-password': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
            `,
            'remove-password': `
                <div class="form-group">
                    <label>Select Protected PDF</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Current Password</label>
                    <input type="password" name="password" required>
                </div>
            `,
            'add-watermark': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Watermark Text</label>
                    <input type="text" name="text" placeholder="CONFIDENTIAL" required>
                </div>
            `,
            'add-image': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Select Image</label>
                    <input type="file" name="image" accept="image/*" required>
                </div>
                <div class="form-group">
                    <label>Page Number</label>
                    <input type="number" name="page" value="1" min="1" required>
                </div>
            `,
            'add-page-numbers': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
                <div class="form-group">
                    <label>Position</label>
                    <select name="position">
                        <option value="bottom-center">Bottom Center</option>
                        <option value="bottom-right">Bottom Right</option>
                        <option value="bottom-left">Bottom Left</option>
                        <option value="top-center">Top Center</option>
                    </select>
                </div>
            `,
            'get-info': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
            `,
            'compress': `
                <div class="form-group">
                    <label>Select PDF File</label>
                    <input type="file" name="file" accept=".pdf" required>
                </div>
            `
        };

        function openTool(tool) {
            currentTool = tool;
            document.getElementById('modalTitle').textContent = tool.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            document.getElementById('formFields').innerHTML = toolForms[tool];
            document.getElementById('toolModal').style.display = 'block';
            document.getElementById('success').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('downloadLink').style.display = 'none';
        }

        function closeModal() {
            document.getElementById('toolModal').style.display = 'none';
            document.getElementById('toolForm').reset();
        }

        document.getElementById('toolForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            document.getElementById('loading').style.display = 'block';
            document.getElementById('success').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('downloadLink').style.display = 'none';

            try {
                const response = await fetch(`/process/${currentTool}`, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                document.getElementById('loading').style.display = 'none';

                if (data.success) {
                    if (data.info) {
                        document.getElementById('success').innerHTML = '<pre>' + JSON.stringify(data.info, null, 2) + '</pre>';
                        document.getElementById('success').style.display = 'block';
                    } else if (data.files) {
                        let html = '<h3>Download Files:</h3>';
                        data.files.forEach(file => {
                            html += `<a href="/download/${file}" download>${file}</a><br>`;
                        });
                        document.getElementById('downloadLink').innerHTML = html;
                        document.getElementById('downloadLink').style.display = 'block';
                        document.getElementById('success').textContent = data.message;
                        document.getElementById('success').style.display = 'block';
                    } else {
                        document.getElementById('downloadLink').innerHTML = `<a href="/download/${data.filename}" download>Download ${data.filename}</a>`;
                        document.getElementById('downloadLink').style.display = 'block';
                        document.getElementById('success').textContent = data.message;
                        document.getElementById('success').style.display = 'block';
                    }
                } else {
                    document.getElementById('error').textContent = data.message;
                    document.getElementById('error').style.display = 'block';
                }
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').textContent = 'Error: ' + error.message;
                document.getElementById('error').style.display = 'block';
            }
        });

        window.onclick = function(event) {
            if (event.target == document.getElementById('toolModal')) {
                closeModal();
            }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return HTML_TEMPLATE


@app.route('/process/<tool>', methods=['POST'])
def process_tool(tool):
    try:
        if tool == 'merge':
            return merge_pdfs()
        elif tool == 'split':
            return split_pdf()
        elif tool == 'extract':
            return extract_pages()
        elif tool == 'rotate':
            return rotate_pdf()
        elif tool == 'remove':
            return remove_pages()
        elif tool == 'organize':
            return organize_pages()
        elif tool == 'image-to-pdf':
            return image_to_pdf()
        elif tool == 'html-to-pdf':
            return html_to_pdf()
        elif tool == 'markdown-to-pdf':
            return markdown_to_pdf()
        elif tool == 'pdf-to-image':
            return pdf_to_image()
        elif tool == 'pdf-to-text':
            return pdf_to_text()
        elif tool == 'pdf-to-html':
            return pdf_to_html()
        elif tool == 'pdf-to-csv':
            return pdf_to_csv()
        elif tool == 'add-password':
            return add_password()
        elif tool == 'remove-password':
            return remove_password()
        elif tool == 'add-watermark':
            return add_watermark()
        elif tool == 'add-image':
            return add_image()
        elif tool == 'add-page-numbers':
            return add_page_numbers()
        elif tool == 'get-info':
            return get_pdf_info()
        elif tool == 'compress':
            return compress_pdf()
        else:
            return jsonify({'success': False, 'message': 'Unknown tool'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def merge_pdfs():
    files = request.files.getlist('files')
    merger = PdfMerger()

    for file in files:
        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(file_path)
            merger.append(file_path)

    output_filename = f'merged_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    merger.write(output_path)
    merger.close()

    return jsonify({'success': True, 'filename': output_filename, 'message': 'PDFs merged successfully!'})


def split_pdf():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    output_files = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        output_filename = f'page_{i + 1}_{uuid.uuid4().hex[:8]}.pdf'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        output_files.append(output_filename)

    return jsonify({'success': True, 'files': output_files, 'message': f'PDF split into {len(output_files)} pages!'})


def extract_pages():
    file = request.files['file']
    pages_str = request.form['pages']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    writer = PdfWriter()

    # Parse page numbers (e.g., "1,3,5-7")
    pages = []
    for part in pages_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start - 1, end))
        else:
            pages.append(int(part) - 1)

    for page_num in pages:
        if 0 <= page_num < len(reader.pages):
            writer.add_page(reader.pages[page_num])

    output_filename = f'extracted_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Pages extracted successfully!'})


def rotate_pdf():
    file = request.files['file']
    angle = int(request.form['angle'])

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    output_filename = f'rotated_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': f'PDF rotated {angle}°!'})


def remove_pages():
    file = request.files['file']
    pages_str = request.form['pages']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    writer = PdfWriter()

    pages_to_remove = set(int(p) - 1 for p in pages_str.split(','))

    for i, page in enumerate(reader.pages):
        if i not in pages_to_remove:
            writer.add_page(page)

    output_filename = f'removed_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Pages removed successfully!'})


def organize_pages():
    file = request.files['file']
    order_str = request.form['order']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    writer = PdfWriter()

    new_order = [int(p) - 1 for p in order_str.split(',')]

    for page_num in new_order:
        if 0 <= page_num < len(reader.pages):
            writer.add_page(reader.pages[page_num])

    output_filename = f'organized_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Pages reorganized successfully!'})


def image_to_pdf():
    files = request.files.getlist('files')
    image_paths = []

    for file in files:
        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(file_path)
            image_paths.append(file_path)

    output_filename = f'images_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as f:
        f.write(img2pdf.convert(image_paths))

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Images converted to PDF!'})


def html_to_pdf():
    try:
        from weasyprint import HTML
    except:
        return jsonify({'success': False, 'message': 'WeasyPrint not installed. Install with: pip install weasyprint'})

    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        html_content = file.read().decode('utf-8')
    else:
        html_content = request.form['html']

    output_filename = f'converted_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    HTML(string=html_content).write_pdf(output_path)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'HTML converted to PDF!'})


def markdown_to_pdf():
    try:
        from weasyprint import HTML
    except:
        return jsonify({'success': False, 'message': 'WeasyPrint not installed. Install with: pip install weasyprint'})

    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        md_content = file.read().decode('utf-8')
    else:
        md_content = request.form['markdown']

    html_content = markdown.markdown(md_content)
    html_template = f"<html><body>{html_content}</body></html>"

    output_filename = f'markdown_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    HTML(string=html_template).write_pdf(output_path)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Markdown converted to PDF!'})


def pdf_to_image():
    try:
        from pdf2image import convert_from_path
    except:
        return jsonify({'success': False, 'message': 'pdf2image not installed. Install with: pip install pdf2image'})

    file = request.files['file']
    img_format = request.form.get('format', 'png')

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    images = convert_from_path(file_path)
    output_files = []

    for i, image in enumerate(images):
        output_filename = f'page_{i + 1}_{uuid.uuid4().hex[:8]}.{img_format}'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        image.save(output_path, img_format.upper())
        output_files.append(output_filename)

    return jsonify({'success': True, 'files': output_files, 'message': f'PDF converted to {len(output_files)} images!'})


def pdf_to_text():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + '\n\n'

    output_filename = f'text_{uuid.uuid4().hex[:8]}.txt'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Text extracted successfully!'})


def pdf_to_html():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + '<br><hr><br>'

    html_content = f"<html><body>{text}</body></html>"

    output_filename = f'converted_{uuid.uuid4().hex[:8]}.html'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'PDF converted to HTML!'})


def pdf_to_csv():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    output_filename = f'tables_{uuid.uuid4().hex[:8]}.csv'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with pdfplumber.open(file_path) as pdf:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        writer.writerow(row)
                    writer.writerow([])  # Empty row between tables

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Tables extracted to CSV!'})


def add_password():
    file = request.files['file']
    password = request.form['password']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    output_filename = f'protected_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Password added successfully!'})


def remove_password():
    file = request.files['file']
    password = request.form['password']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)

    if reader.is_encrypted:
        reader.decrypt(password)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output_filename = f'unlocked_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Password removed successfully!'})


def add_watermark():
    file = request.files['file']
    watermark_text = request.form['text']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    # Create watermark PDF
    watermark_filename = f'watermark_{uuid.uuid4().hex[:8]}.pdf'
    watermark_path = os.path.join(app.config['UPLOAD_FOLDER'], watermark_filename)

    c = canvas.Canvas(watermark_path, pagesize=letter)
    c.setFont("Helvetica", 40)
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
    c.saveState()
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    c.save()

    # Apply watermark
    reader = PdfReader(file_path)
    watermark_reader = PdfReader(watermark_path)
    watermark_page = watermark_reader.pages[0]

    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    output_filename = f'watermarked_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Watermark added successfully!'})


def add_image():
    file = request.files['file']
    image_file = request.files['image']
    page_num = int(request.form['page']) - 1

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image_file.filename))

    file.save(file_path)
    image_file.save(image_path)

    # Create image overlay PDF
    overlay_filename = f'overlay_{uuid.uuid4().hex[:8]}.pdf'
    overlay_path = os.path.join(app.config['UPLOAD_FOLDER'], overlay_filename)

    c = canvas.Canvas(overlay_path, pagesize=letter)
    img = ImageReader(image_path)
    c.drawImage(img, 100, 100, width=200, height=200, preserveAspectRatio=True)
    c.save()

    # Merge with original
    reader = PdfReader(file_path)
    overlay_reader = PdfReader(overlay_path)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if i == page_num:
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    output_filename = f'with_image_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Image added successfully!'})


def add_page_numbers():
    file = request.files['file']
    position = request.form.get('position', 'bottom-center')

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    output_filename = f'numbered_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    # Create numbered pages
    temp_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{uuid.uuid4().hex[:8]}.pdf')
    c = canvas.Canvas(temp_pdf, pagesize=letter)

    for i in range(len(reader.pages)):
        c.setFont("Helvetica", 10)

        if 'bottom' in position:
            y = 30
        else:
            y = 800

        if 'center' in position:
            x = 300
        elif 'right' in position:
            x = 550
        else:
            x = 50

        c.drawString(x, y, str(i + 1))
        c.showPage()

    c.save()

    # Merge page numbers
    number_reader = PdfReader(temp_pdf)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        page.merge_page(number_reader.pages[i])
        writer.add_page(page)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    return jsonify({'success': True, 'filename': output_filename, 'message': 'Page numbers added successfully!'})


def get_pdf_info():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)

    info = {
        'Pages': len(reader.pages),
        'Encrypted': reader.is_encrypted,
        'File Size': f"{os.path.getsize(file_path) / 1024:.2f} KB"
    }

    if reader.metadata:
        for key, value in reader.metadata.items():
            info[key] = str(value)

    return jsonify({'success': True, 'info': info, 'message': 'PDF information retrieved!'})


def compress_pdf():
    file = request.files['file']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(file_path)

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)

    output_filename = f'compressed_{uuid.uuid4().hex[:8]}.pdf'
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    original_size = os.path.getsize(file_path)
    compressed_size = os.path.getsize(output_path)
    reduction = ((original_size - compressed_size) / original_size) * 100

    return jsonify({
        'success': True,
        'filename': output_filename,
        'message': f'PDF compressed! Size reduced by {reduction:.1f}%'
    })


@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['OUTPUT_FOLDER'], filename),
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 PDF Multi-Tool Editor Starting...")
    print("=" * 60)
    print("\n📍 Access the application at: http://127.0.0.1:5000")
    print("\n⚙️  Available Features:")
    print("   • Merge, Split, Extract, Rotate PDFs")
    print("   • Convert Images/HTML/Markdown to PDF")
    print("   • Convert PDF to Images/Text/HTML/CSV")
    print("   • Add Password, Watermarks, Page Numbers")
    print("   • Remove Password, Compress, Get Info")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
