import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import subprocess  # To run model.py script

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}  # can add more if needed

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Renders the homepage (nexora.html)"""
    return render_template('nexora.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_and_process():
    """
    Handles file upload, saves the file, calls model.py for processing,
    and returns the result.
    """
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file part'}), 400
        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # 1. Call model.py script using subprocess
                #    and pass the filepath as an argument.
                #    Capture the output (stdout and stderr).
                result = subprocess.run(
                    ['python', 'model.py', filepath],  # Pass the file path
                    capture_output=True,
                    text=True,  # Get output as text, not bytes
                    check=True # Raise an exception for non-zero exit code
                )
                output_from_model = result.stdout  # Get the output from model.py
                error_from_model = result.stderr

                if error_from_model:
                    print(f"Error from model.py: {error_from_model}") # print the error

                # 2.  Return the output from model.py to the client
                return jsonify({'result': output_from_model}), 200

            except subprocess.CalledProcessError as e:
                # Handle errors from the subprocess (e.g., model.py crashing)
                error_message = f"Error running model.py: {e.stderr}"
                print(error_message)
                return jsonify({'error': error_message}), 500  # Internal Server Error
            except Exception as e:
                # Handle other potential errors (e.g., file issues)
                error_message = f"An error occurred: {str(e)}"
                print(error_message)
                return jsonify({'error': error_message}), 500

        else:
            return jsonify({'error': 'Invalid file type'}), 400

    #  GET request:  render the upload form
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)