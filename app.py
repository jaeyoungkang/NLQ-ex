from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World! GA4 Analyzer is working!"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)