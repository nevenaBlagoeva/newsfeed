from sources.config import SOURCES
import json
import boto3
import os

# Initialize SQS client at module level
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    print(f"Starting fetcher lambda with {len(SOURCES)} sources")
    
    # Get queue URL from environment variable
    queue_url = os.getenv('SQS_QUEUE_URL')
    if not queue_url:
        raise ValueError("SQS_QUEUE_URL environment variable not set")
    
    all_events = []
    
    for source_config in SOURCES:
        try:
            source_class = source_config["class"]
            config = source_config["config"]
            
            # Instantiate the fetcher with its config
            fetcher = source_class(**config)
            
            # Fetch articles
            events = fetcher.fetch()
            all_events.extend(events)
            
        except Exception as e:
            print(f"ERROR: Source {source_config.get('name', 'unknown')} failed: {str(e)}")

    # Send events to SQS
    sent_count = 0
    for event in all_events:
        try:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(event),
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send event to SQS: {str(e)}")

    print(f"Completed: fetched {len(all_events)} events, sent {sent_count} to SQS")
