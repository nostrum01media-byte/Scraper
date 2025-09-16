# Media Scraper App

import os
import requests
from flask import Flask, jsonify, send_file

app = Flask(__name__)

@app.route('/media/<path:filename>', methods=['GET'])
def get_media(filename):
    # Logic to retrieve media file
    media_path = os.path.join('media', filename)
    if os.path.exists(media_path):
        return send_file(media_path)
    return jsonify({'error': 'File not found'}), 404

@app.route('/media/previews', methods=['GET'])
def get_media_previews():
    # Logic to show media previews
    media_files = os.listdir('media')
    previews = [{'filename': f, 'preview_url': f'/media/{f}'} for f in media_files]
    return jsonify(previews)

@app.route('/media/download/<path:filename>', methods=['GET'])
def download_file(filename):
    media_path = os.path.join('media', filename)
    if os.path.exists(media_path):
        return send_file(media_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/media/download/zip', methods=['GET'])
def download_zip():
    # Logic to create a ZIP file
    from zipfile import ZipFile
    import io

    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, 'w') as zip_file:
        for filename in os.listdir('media'):
            zip_file.write(os.path.join('media', filename), filename)
    zip_buffer.seek(0)
    return send_file(zip_buffer, attachment_filename='media.zip', as_attachment=True)

@app.route('/media/raw/<path:filename>', methods=['GET'])
def get_raw_url(filename):
    media_path = os.path.join('media', filename)
    if os.path.exists(media_path):
        return jsonify({'raw_url': f'/media/{filename}'}), 200
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)