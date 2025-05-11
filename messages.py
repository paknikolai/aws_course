import boto3
import json

from botocore.config import Config

config = Config(
    region_name = 'eu-north-1'
)

sqs = boto3.client('sqs', config=config)
sns = boto3.client('sns', config=config)
s3 = boto3.client('s3')

sns_info = {}

def subscribe_email(email):
    try:
        response = sns.subscribe(
            TopicArn=sns_info["SNS_TOPIC_ARN"],
            Protocol='email',
            Endpoint=email
        )
        print(f"Subscription initiated for {email}. Confirmation pending.")
        return True, "Subscription initiated. Please check your email to confirm."
    except Exception as e:
        print(f"Error subscribing {email}: {e}")
        return False, f"Error subscribing: {e}"

def unsubscribe_email(email):
    try:
        subscriptions = sns.list_subscriptions_by_topic(TopicArn=sns_info["SNS_TOPIC_ARN"])['Subscriptions']
        subscription_arn_to_unsubscribe = None
        for sub in subscriptions:
            if sub['Endpoint'] == email and sub['Protocol'] == 'email':
                subscription_arn_to_unsubscribe = sub['SubscriptionArn']
                break

        if subscription_arn_to_unsubscribe:
            response = sns.unsubscribe(
                SubscriptionArn=subscription_arn_to_unsubscribe
            )
            print(f"Unsubscribed {email}.")
            return True, "Successfully unsubscribed."
        else:
            return False, f"Email {email} is not subscribed to this topic."
    except Exception as e:
        print(f"Error unsubscribing {email}: {e}")
        return False, f"Error unsubscribing: {e}"

def publish_image_upload_notification(bucket_name, info):
    try:
        message = {
            'event': 'image_uploaded',
            'info': info
        }
        key = info["name"]

        sqs.send_message(
            QueueUrl=sns_info["SQS_QUEUE_URL"],
            MessageBody=json.dumps(message)
        )
        print(f"Published image upload notification for {key} to SQS.")
    except Exception as e:
        print(f"Error publishing notification for {key}: {e}")
