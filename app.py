import gradio as gr
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import json
import os
import uuid
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Flask app
flask_app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF (digital or scanned)"""
    results = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Try direct text extraction
                text = page.extract_text()
                
                if text and len(text.strip()) > 50:
                    results.append({
                        "page": page_num + 1,
                        "text": text,
                        "method": "digital"
                    })
                else:
                    # Use OCR for scanned pages
                    images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1, dpi=150)
                    if images:
                        ocr_text = pytesseract.image_to_string(images[0])
                        results.append({
                            "page": page_num + 1,
                            "text": ocr_text if ocr_text else "[No text found]",
                            "method": "ocr"
                        })
                    else:
                        results.append({
                            "page": page_num + 1,
                            "text": "[Could not process page]",
                            "method": "error"
                        })
    except Exception as e:
        return [{"page": 0, "text": f"Error: {str(e)}", "method": "error"}]
    
    return results

@flask_app.route('/ingest', methods=['POST'])
def ingest_pdf():
    """API endpoint for PDF processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    temp_path = f"/tmp/{uuid.uuid4()}_{filename}"
    file.save(temp_path)
    
    try:
        results = extract_text_from_pdf(temp_path)
        
        result_id = str(uuid.uuid4())
        output_path = f"/tmp/{result_id}.json"
        
        with open(output_path, 'w') as f:
            json.dump({
                "filename": filename,
                "results": results,
                "total_pages": len(results)
            }, f, indent=2)
        
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
    """Download extracted results as JSON"""
    output_path = f"/tmp/{result_id}.json"
    if os.path.exists(output_path):
        return send_file(
            output_path, 
            as_attachment=True, 
            download_name=f"extracted_{result_id}.json",
            mimetype='application/json'
        )
    return jsonify({'error': 'Result not found'}), 404

@flask_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Gradio UI
def process_pdf(file):
    if file is None:
        return "Please upload a PDF file"
    
    results = extract_text_from_pdf(file.name)
    
    output = []
    for r in results:
        output.append(f"\n{'='*60}")
        output.append(f"📄 PAGE {r['page']} (Method: {r['method'].upper()})")
        output.append(f"{'='*60}")
        output.append(r['text'])
    
    return "\n".join(output)

# Create Gradio interface
with gr.Blocks(title="PDF Extractor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📄 PDF Text Extractor")
    gr.Markdown("Upload any PDF - extracts text from both digital and scanned documents")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
        output_text = gr.Textbox(label="Extracted Text", lines=25, max_lines=50)
    
    pdf_input.change(process_pdf, inputs=pdf_input, outputs=output_text)
    
    gr.Markdown("---")
    gr.Markdown("### 📡 API Usage")
    gr.Markdown("```bash\ncurl -F file=@document.pdf https://your-app.onrender.com/ingest\n```")

# Start both servers
if __name__ == "__main__":
    import threading
    
    # Run Flask in background thread
    def run_flask():
        flask_app.run(host='0.0.0.0', port=5001, threaded=True)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run Gradio on main port
    demo.launch(server_name="0.0.0.0", server_port=10000)
