import boto3
import json

sqs = boto3.client('sqs')
sns = boto3.client('sns')
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

def publish_image_upload_notification(bucket_name, key):
    try:
        
        download_link = "link"

        message = {
            'event': 'image_uploaded',
            'download_link': download_link
        }

        sqs.send_message(
            QueueUrl=sns_info["SQS_QUEUE_URL"],
            MessageBody=json.dumps(message)
        )
        print(f"Published image upload notification for {key} to SQS.")
    except Exception as e:
        print(f"Error publishing notification for {key}: {e}")

def process_sqs_messages():
    print("Processing SQS messages...")
    try:
        response = sqs.receive_message(
            QueueUrl=sns_info["SQS_QUEUE_URL"],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20 # Enable long polling
        )

        messages = response.get('Messages', [])
        for message in messages:
            try:
                body = json.loads(message['Body'])
                if body.get('event') == 'image_uploaded':
                    image_name = body['name']
                    # image_size = body['size']
                    # image_extension = body['extension']
                    # download_link = body['download_link']

                    sns_message = "message"

                    sns.publish(
                        TopicArn=sns_info["SNS_TOPIC_ARN"],
                        Message=sns_message
                    )
                    print(f"Published notification for {image_name} to SNS.")

                sqs.delete_message(
                    QueueUrl=sns_info["SQS_QUEUE_URL"],
                    ReceiptHandle=message['ReceiptHandle']
                )
            except json.JSONDecodeError:
                print(f"Error decoding SQS message: {message['Body']}")
                # Optionally, send to a dead-letter queue or handle differently
                sqs.delete_message(
                    QueueUrl=sns_info["SQS_QUEUE_URL"],
                    ReceiptHandle=message['ReceiptHandle']
                )
            except Exception as e:
                print(f"Error processing SQS message: {e}")
                # Consider error handling/logging

    except Exception as e:
        print(f"Error receiving SQS messages: {e}")