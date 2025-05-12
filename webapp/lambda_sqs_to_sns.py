import json
import os
import boto3

sns_client = boto3.client('sns')
sns_info = {}
sns_info["SNS_TOPIC_ARN"] = "arn:aws:sns:eu-north-1:971422678291:web-app-pak-nikolai-app-UploadsNotificationTopic"

def process_sqs_messages(messages):
    print("Processing SQS messages...")

    for message in messages:
        try:
            body = json.loads(message['body'])
            if body.get('event') == 'image_uploaded':
                info = body['info']
                image_name = info["name"]

                sns_message = json.dumps(info, default=str)

                sns_client.publish(
                    TopicArn=sns_info["SNS_TOPIC_ARN"],
                    Message=sns_message
                )
                print(f"Published notification for {image_name} to SNS.")

        except Exception as e:
            print(f"Error processing SQS message: {e}")

def lambda_handler(event, context):
    process_sqs_messages(event['Records'])
    return {
        'statusCode': 200,
        'body': json.dumps('SQS messages processed successfully.')
    }