"""
Ultra Simple Test Server - Just to verify Flask works
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(static_folder, path)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Simple server running'})

if __name__ == '__main__':
    print("\n✅ Simple server starting on http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
