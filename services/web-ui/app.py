# services/web-ui/app.py
from flask import Flask, send_from_directory, jsonify
import os

# static_folder를 명시적으로 설정
app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "web-ui"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)