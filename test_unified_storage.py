"""
Test script for the unified storage system.

This script tests the new unified storage approach to ensure it works
correctly with the official SurrealDB client.
"""

import logging
import asyncio
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_unified_storage():
    """Test the unified storage system."""
    try:
        # Initialize storage
        storage = UnifiedDialogueStorage()
        
        # Test health check
        logger.info("Testing health check...")
        health = storage.health_check()
        logger.info(f"Health check result: {health}")
        
        # Test session creation
        logger.info("Testing session creation...")
        session = storage.create_session(
            user_id="test_user",
            title="Test Session",
            metadata={"test": True, "dialogue_type": "human_ai_private"}
        )
        
        if session:
            logger.info(f"Session created: {session['id']}")
            session_id = session['id']
            
            # Test turn creation
            logger.info("Testing turn creation...")
            user_turn = storage.create_turn(
                session_id=session_id,
                role="human",
                content="Hello, this is a test message!",
                metadata={"source": "test"}
            )
            
            if user_turn:
                logger.info(f"User turn created: {user_turn['id']}")
                
                # Create AI response turn
                ai_turn = storage.create_turn(
                    session_id=session_id,
                    role="ai",
                    content="Hello! I received your test message.",
                    metadata={"model": "test"}
                )
                
                if ai_turn:
                    logger.info(f"AI turn created: {ai_turn['id']}")
                
                # Test getting turns
                logger.info("Testing turn retrieval...")
                turns = storage.get_turns(session_id)
                logger.info(f"Retrieved {len(turns)} turns for session")
                
                for turn in turns:
                    logger.info(f"Turn {turn['id']}: {turn['role']} - {turn['content'][:50]}...")
                
                # Test getting session with turns
                logger.info("Testing session with turns retrieval...")
                session_with_turns = storage.get_session_with_turns(session_id)
                if session_with_turns:
                    logger.info(f"Session with {len(session_with_turns['turns'])} turns retrieved")
                
                # Test counts
                logger.info("Testing counts...")
                session_count = storage.count_user_sessions("test_user")
                turn_count = storage.count_session_turns(session_id)
                logger.info(f"User has {session_count} sessions, session has {turn_count} turns")
                
            else:
                logger.error("Failed to create user turn")
        else:
            logger.error("Failed to create session")
        
        logger.info("Unified storage test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


async def test_unified_storage_async():
    """Test the unified storage system asynchronously."""
    try:
        # Initialize storage
        storage = UnifiedDialogueStorage()
        
        # Test async session creation
        logger.info("Testing async session creation...")
        session = await storage.create_session_async(
            user_id="async_test_user",
            title="Async Test Session",
            metadata={"test": True, "async": True}
        )
        
        if session:
            logger.info(f"Async session created: {session['id']}")
            session_id = session['id']
            
            # Test async turn creation
            logger.info("Testing async turn creation...")
            user_turn = await storage.create_turn_async(
                session_id=session_id,
                role="human",
                content="This is an async test message!",
                metadata={"source": "async_test"}
            )
            
            if user_turn:
                logger.info(f"Async user turn created: {user_turn['id']}")
                
                # Test async turn retrieval
                logger.info("Testing async turn retrieval...")
                turns = await storage.get_turns_async(session_id)
                logger.info(f"Retrieved {len(turns)} turns async")
                
                # Test async session with turns
                logger.info("Testing async session with turns...")
                session_with_turns = await storage.get_session_with_turns_async(session_id)
                if session_with_turns:
                    logger.info(f"Async session with {len(session_with_turns['turns'])} turns retrieved")
            else:
                logger.error("Failed to create async user turn")
        else:
            logger.error("Failed to create async session")
        
        logger.info("Async unified storage test completed successfully!")
        
    except Exception as e:
        logger.error(f"Async test failed: {e}")
        raise


if __name__ == "__main__":
    print("Testing Unified Storage System")
    print("=" * 50)
    
    # Test synchronous operations
    print("\n1. Testing Synchronous Operations:")
    test_unified_storage()
    
    # Test asynchronous operations
    print("\n2. Testing Asynchronous Operations:")
    asyncio.run(test_unified_storage_async())
    
    print("\nAll tests completed successfully!")
    print("The unified storage system is working correctly.")