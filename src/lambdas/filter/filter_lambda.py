import json
import boto3
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
filtered_table_name = os.getenv('FILTERED_TABLE_NAME')
filtered_table = dynamodb.Table(filtered_table_name) if filtered_table_name else None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    print(f"Processing {len(event['Records'])} DynamoDB stream records")
    
    if not filtered_table:
        raise ValueError("FILTERED_TABLE_NAME environment variable not set")
    
    processed = 0
    
    for record in event['Records']:
        try:
            # Extract the new item from the stream record
            raw_item = record['dynamodb']['NewImage']
            print(raw_item)            
            # Convert DynamoDB format to regular dict
            item = dynamodb_to_dict(raw_item)
            print(f"Processing item: {item.get('title', 'No Title')[:50]}...")
            # Apply filtering logic
            if should_filter_item(item):
                # Calculate rank and create filtered item
                filtered_item = create_filtered_item(item)
                
                # Save to filtered events table
                filtered_table.put_item(Item=filtered_item)
                processed += 1
                print(f"Filtered item saved: {item['title'][:50]}...")
                
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            # Continue processing other records
            continue
    
    print(f"Processed {processed} items through filter")
    return {"processed": processed}

def dynamodb_to_dict(dynamodb_item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DynamoDB item format to regular Python dict"""
    result = {}
    for key, value in dynamodb_item.items():
        if 'S' in value:  # String
            result[key] = value['S']
        elif 'N' in value:  # Number
            result[key] = int(value['N']) if value['N'].isdigit() else float(value['N'])
        # Add other type conversions as needed
    return result

def should_filter_item(item: Dict[str, Any]) -> bool:
    """Apply filtering logic - basic keyword filtering for now"""
    title = item.get('title', '').lower()
    body = item.get('body', '').lower()
    
    # Simple keyword filtering
    tech_keywords = ['python', 'javascript', 'programming', 'development', 'software', 'technology', 'ai', 'machine learning']
    
    return any(keyword in title or keyword in body for keyword in tech_keywords)

def create_filtered_item(raw_item: Dict[str, Any]) -> Dict[str, Any]:
    """Create filtered item with ranking"""
    # Calculate relevance score
    relevance_score = calculate_relevance_score(raw_item)
    
    # Create sort key with relevance and timestamp
    published_at = raw_item.get('published_at', datetime.now(timezone.utc).isoformat())
    sort_key = f"{relevance_score:.2f}#{published_at}"
    
    return {
        'PK': 'news',  # Single partition for all filtered items
        'SK': sort_key,  # Sort key with relevance and timestamp
        'id': raw_item['id'],
        'source': raw_item['source'],
        'title': raw_item['title'],
        'body': raw_item.get('body', ''),
        'published_at': published_at,
        'relevance_score': Decimal(str(relevance_score)),  # Convert to Decimal needed for DynamoDB
        'filtered_at': datetime.now(timezone.utc).isoformat(),
        'ttl_epoch': int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)  # 30 days
    }

def calculate_relevance_score(item: Dict[str, Any]) -> float:
    """Calculate relevance score for the item (0.0 - 1.0)"""
    score = 0.0
    
    # Score based on source (Reddit gets higher score)
    if item.get('source') == 'reddit':
        reddit_score = min(item.get('score', 0), 1000) / 1000  # Normalize to 0-1
        score += reddit_score * 0.3  # 30% weight
    
    # Score based on recency (newer items get higher score)
    try:
        published_at = datetime.fromisoformat(item.get('published_at', ''))
        hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        recency_score = max(0, 1 - (hours_old / 24))  # Decay over 24 hours
        score += recency_score * 0.4  # 40% weight
    except:
        score += 0.2  # Default recency score
    
    # Score based on title keywords
    title = item.get('title', '').lower()
    high_value_keywords = ['breaking', 'new', 'release', 'announcement']
    keyword_score = min(sum(0.1 for keyword in high_value_keywords if keyword in title), 0.3)
    score += keyword_score  # Up to 30% weight
    
    return min(max(score, 0.0), 1.0)  # Ensure 0.0 - 1.0 range
