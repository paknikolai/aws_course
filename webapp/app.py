from flask import Flask, render_template, jsonify, request
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)
s3 = boto3.client('s3')
BUCKET_NAME = 'web-site-pak-nikolai'

def get_metadata(image_name):
    try:
        response = s3.head_object(Bucket=BUCKET_NAME, Key=image_name)
        return response['Metadata']
    except s3.exceptions.NoSuchKey:
        return None

@app.route('/download/<image_name>', methods=['GET'])
def download_image(image_name):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=image_name)
        return response['Body'].read(), 200
    except s3.exceptions.NoSuchKey:
        return "Image not found", 404

@app.route('/metadata/<image_name>', methods=['GET'])
def show_metadata(image_name):
    metadata = get_metadata(image_name)
    if metadata:
        return jsonify(metadata), 200
    else:
        return "Image not found", 404

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    try:
        s3.upload_fileobj(file, BUCKET_NAME, file.filename)
        return "File uploaded successfully", 200
    except NoCredentialsError:
        return "AWS credentials not found", 403

@app.route('/delete/<image_name>', methods=['DELETE'])
def delete_image(image_name):
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=image_name)
        return "Image deleted successfully", 200
    except s3.exceptions.NoSuchKey:
        return "Image not found", 404

def get_region():
    try:
        from ec2_metadata import ec2_metadata
        return f"region: {ec2_metadata.region} AZ: {ec2_metadata.availability_zone}"
    except Exception as e:
        return "can't get region because of " + repr(e)

@app.route("/")
def index():
    message = get_region()
    return render_template("index.html", message=message)

@app.route("/health")
def health_check():
    """Endpoint for health checks."""
    return jsonify({"status": get_region()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)