# services/web-ui/app.py
from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "web-ui"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)