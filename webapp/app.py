from flask import Flask, render_template, jsonify, request, send_file
import boto3
from botocore.exceptions import NoCredentialsError
import pymysql
import argparse
import os

app = Flask(__name__)
s3 = boto3.client('s3')
BUCKET_NAME = 'web-site-pak-nikolai'

session = boto3.session.Session()
db_info = {}

def get_metadata(image_name):
    try:
        response = s3.head_object(Bucket=BUCKET_NAME, Key=image_name)
        metadata = {}
        metadata["last_modified"] = response['LastModified']
        metadata["file_size"] = response['ContentLength']
        metadata["file_extension"] = os.path.splitext(image_name)[1]
        metadata["file_name"] = image_name
        return metadata
    except s3.exceptions.NoSuchKey:
        return f"{image_name} not found in bucket {BUCKET_NAME}" #None

@app.route('/download/<image_name>', methods=['GET'])
def download_image(image_name):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=image_name)
        return send_file(response['Body'], as_attachment=True, download_name=image_name)
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
        add_metadata_to_db(get_metadata(file.filename))
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

def add_metadata_to_db(metadata):
    db_host = db_info["db_host"]
    db_user = db_info["db_user"]
    db_password = db_info["db_password"]
    db_name = db_info["db_name"]

    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection:
        with connection.cursor() as cursor:
            # Create table (if needed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_name VARCHAR(255),
                    file_extension VARCHAR(255),
                    file_size VARCHAR(255),
                    last_modified VARCHAR(255)
                )
            """)
            # Insert data
            cursor.execute("INSERT INTO images (file_name, file_extension, file_size, last_modified) VALUES (%s, %s, %s, %s)",
                           (metadata["file_name"], metadata["file_extension"], metadata["file_size"], metadata["last_modified"]))
            cursor.execute(f'SELECT * FROM {db_info["db_name"]}')
            print(cursor.fetchall())
            connection.commit()

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_host",
        required=True,
        help="db_host"
    )

    parser.add_argument(
        "--db_user",
        required=True,
        help="db_user"
    )

    parser.add_argument(
        "--db_password",
        required=True,
        help="db_password"
    )

    parser.add_argument(
        "--db_name",
        required=True,
        help="db_name"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = get_arguments()

    db_info["db_host"] = args.db_host
    db_info["db_user"] = args.db_user
    db_info["db_password"] = args.db_password
    db_info["db_name"] = args.db_name

    conn = pymysql.connect(host=db_info["db_host"],
                       user=db_info["db_user"],
                       password=db_info["db_password"])

    conn.cursor().execute(f'CREATE DATABASE IF NOT EXISTS {db_info["db_name"]}')

    app.run(host="0.0.0.0", port=8080)
    # python3 app.py  --db_user  --db_password  --db_name images --db_host 