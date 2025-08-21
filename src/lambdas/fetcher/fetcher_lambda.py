from sources.config import SOURCES
import json

def lambda_handler(event, context):
    print(f"Lambda started with event: {json.dumps(event)}")
    
    all_events = []
    
    for source_config in SOURCES:
        try:
            source_name = source_config["name"]
            source_class = source_config["class"]
            config = source_config["config"]
            
            print(f"Processing source: {source_name}")
            
            # Instantiate the fetcher with its config
            fetcher = source_class(**config)
            
            # Fetch articles
            events = fetcher.fetch()
            print(f"Source {source_name} returned {len(events)} events")
            
            all_events.extend(events)
            
        except Exception as e:
            print(f"ERROR: Source {source_config.get('name', 'unknown')} failed: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

    print(f"Total fetched {len(all_events)} events from {len(SOURCES)} sources.")
    
    # Print first few events as sample
    for i, event in enumerate(all_events[:3]):
        print(f"Event {i+1}: {json.dumps(event, indent=2)}")

    return {
        "status": "ok", 
        "count": len(all_events),
        "sources_processed": len(SOURCES)
    }
