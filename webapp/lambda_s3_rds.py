      
import os
import json
import boto3
import pymysql


DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

db_connection = None

def get_metadata(image_name):
    try:
        print(f"Getting metadata for image: {image_name}")
        s3 = boto3.client('s3', region_name='eu-north-1')
        print("Connected to S3")
        response = s3.head_object(Bucket=BUCKET_NAME, Key=image_name)
        print("Retrieved metadata from S3")
        metadata = {}
        metadata["last_modified"] = str(response['LastModified'])
        metadata["file_size"] = response['ContentLength']
        metadata["file_extension"] = os.path.splitext(image_name)[1]
        metadata["file_name"] = image_name
        print("Metadata retrieved")
        return metadata
    except s3.exceptions.NoSuchKey:
        return f"{image_name} not found in bucket {BUCKET_NAME}" #None

def get_db_connection():
    global db_connection
    if not db_connection:
        try:
            db_connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME, connect_timeout=5)
        except pymysql.Error as e:
            print(f"ERROR: Could not connect to MySQL instance: {e}")
            raise e
    return db_connection

def compare_metadata(db_metadata, s3_metadata):
    consistent = True
    for key, value in db_metadata.items():
        if key not in s3_metadata or s3_metadata[key] != value:
            consistent = False
            break
    return consistent

def lambda_handler(event, context):
    print(f"Event received: {event}")

    log_source = "unknown"
    if 'detail-type' in event:
        log_source = event['detail-type']
    elif 'httpMethod' in event:
        log_source = "api_gateway"
    elif 'requestContext' in event:
        log_source = "web_application"

    print(f"Lambda invoked by: {log_source}")

    
    print("Connecting to database")
    conn = get_db_connection()
    print("Connected to database")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_name, file_extension, file_size, last_modified FROM images")
        column_names = [col[0] for col in cursor.description]
        db_images = []
        for row in cursor.fetchall():
            db_images.append(dict(zip(column_names, row)))
        print("Retrieved data from database")
        is_consistent = True
        for image_data in db_images:
            print(f"Processing image: {image_data['file_name']}")
            metadata = get_metadata(image_data["file_name"])
            is_image_data_consistent = compare_metadata(image_data, metadata)
            print(f"Image data consistent: {is_image_data_consistent}")
            is_consistent &= is_image_data_consistent
        print("Metadata comparison completed")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'data_consistent': is_consistent,
                'log_source': log_source
            })
        }

    except pymysql.Error as e:
        print(f"Database error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Database error: {e}", 'log_source': log_source})
        }
    except Exception as e:
        print(f"General error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"General error: {e}", 'log_source': log_source})
        }
    finally:
        if conn:
            conn.close()
