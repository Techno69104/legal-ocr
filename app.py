import gradio as gr
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import json
import os
import uuid
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import io

# Flask app for API
flask_app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    """Extract text using pdfplumber (digital PDFs) or OCR (scanned)"""
    results = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Try to extract text directly
            text = page.extract_text()
            
            if text and len(text.strip()) > 20:
                # Digital PDF with text
                results.append({
                    "page": page_num + 1,
                    "text": text,
                    "method": "native"
                })
            else:
                # Scanned page - use OCR
                images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1, dpi=200)
                if images:
                    ocr_text = pytesseract.image_to_string(images[0])
                    results.append({
                        "page": page_num + 1,
                        "text": ocr_text,
                        "method": "ocr"
                    })
    
    return results

@flask_app.route('/ingest', methods=['POST'])
def ingest_pdf():
    """API endpoint to process PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    temp_path = f"/tmp/{uuid.uuid4()}_{filename}"
    file.save(temp_path)
    
    try:
        results = extract_text_from_pdf(temp_path)
        
        # Save results
        result_id = str(uuid.uuid4())
        output_path = f"/tmp/{result_id}.json"
        with open(output_path, 'w') as f:
            json.dump({
                "filename": filename,
                "results": results,
                "total_pages": len(results)
            }, f)
        
        return jsonify({
            "success": True,
            "result_id": result_id,
            "download_url": f"/download/{result_id}",
            "pages": len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@flask_app.route('/download/<result_id>', methods=['GET'])
def download_result(result_id):
    """Download extracted JSON results"""
    output_path = f"/tmp/{result_id}.json"
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True, download_name=f"extracted_{result_id}.json")
    return jsonify({'error': 'Result not found'}), 404

# Gradio UI Function
def process_uploaded_pdf(file):
    """Process PDF and return text for Gradio UI"""
    if file is None:
        return "Please upload a PDF file"
    
    results = extract_text_from_pdf(file.name)
    
    output = []
    for result in results:
        output.append(f"📄 Page {result['page']} ({result['method']}):")
        output.append(result['text'])
        output.append("-" * 50)
    
    return "\n".join(output)

# Create Gradio interface
with gr.Blocks(title="PDF Text Extractor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📄 PDF Text Extractor")
    gr.Markdown("Extract text from any PDF - digital or scanned")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
        output_text = gr.Textbox(label="Extracted Text", lines=20)
    
    pdf_input.change(process_uploaded_pdf, inputs=pdf_input, outputs=output_text)
    
    gr.Markdown("### API Usage")
    gr.Markdown("```bash\ncurl -F file=@document.pdf https://your-app.onrender.com/ingest\n```")

# For Render deployment
if __name__ == "__main__":
    import threading
    import uvicorn
    
    # Run Flask in a separate thread for API
    def run_flask():
        flask_app.run(host='0.0.0.0', port=5001)
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Run Gradio on main port
    demo.launch(server_name="0.0.0.0", server_port=10000)
