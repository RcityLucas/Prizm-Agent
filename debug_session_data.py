#!/usr/bin/env python3
"""
Debug script to check sessions and turns data in SurrealDB
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rainbow_agent.storage.surreal.unified_client import UnifiedSurrealClient
from rainbow_agent.config.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Get config
        storage_config = settings.get("storage", {})
        
        # Create client
        client = UnifiedSurrealClient(
            url=storage_config.get("url", "ws://localhost:8000/rpc"),
            namespace=storage_config.get("namespace", "rainbow"),
            database=storage_config.get("database", "test"),
            username=storage_config.get("username", "root"),
            password=storage_config.get("password", "root")
        )
        
        # Check sessions table
        print("=== SESSIONS TABLE ===")
        sessions = client.get_records("sessions", limit=100)
        print(f"Total sessions found: {len(sessions)}")
        
        for i, session in enumerate(sessions):
            print(f"\nSession {i+1}:")
            print(f"  ID: {session.get('id', 'N/A')}")
            print(f"  User ID: {session.get('user_id', 'N/A')}")
            print(f"  Title: {session.get('title', 'N/A')}")
            print(f"  Created: {session.get('created_at', 'N/A')}")
            print(f"  Status: {session.get('status', 'N/A')}")
        
        # Check turns table
        print("\n=== TURNS TABLE ===")
        turns = client.get_records("turns", limit=100)
        print(f"Total turns found: {len(turns)}")
        
        # Group turns by session
        turns_by_session = {}
        for turn in turns:
            session_id = turn.get('session_id', 'unknown')
            if session_id not in turns_by_session:
                turns_by_session[session_id] = []
            turns_by_session[session_id].append(turn)
        
        for session_id, session_turns in turns_by_session.items():
            print(f"\nSession {session_id}: {len(session_turns)} turns")
            for i, turn in enumerate(session_turns):
                print(f"  Turn {i+1}:")
                print(f"    ID: {turn.get('id', 'N/A')}")
                print(f"    Role: {turn.get('role', 'N/A')}")
                print(f"    Content: {turn.get('content', 'N/A')[:100]}...")
                print(f"    Created: {turn.get('created_at', 'N/A')}")
        
        # Test a specific session lookup
        if sessions:
            test_session_id = sessions[0].get('id')
            print(f"\n=== TESTING SESSION LOOKUP ===")
            print(f"Looking up session: {test_session_id}")
            
            # Test direct lookup
            found_session = client.get_records("sessions", f"id = '{test_session_id}'")
            print(f"Direct lookup result: {len(found_session)} records")
            
            if found_session:
                print(f"Found session: {found_session[0].get('title', 'N/A')}")
            else:
                print("❌ Session not found in direct lookup!")
                
        # Test table schema
        print("\n=== TABLE SCHEMAS ===")
        try:
            schema_result = client.execute_sql("INFO FOR DB;")
            print("Database info:")
            print(schema_result)
        except Exception as e:
            print(f"Could not get schema info: {e}")
        
    except Exception as e:
        logger.error(f"Debug script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()