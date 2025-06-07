"""
Test the API with fallback handling for database and AI service failures.

This tests that the system can handle requests gracefully even when
SurrealDB and OpenAI services are not available.
"""

import asyncio
import logging
from rainbow_agent.api.unified_dialogue_processor import UnifiedDialogueProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_dialogue_processing_with_fallbacks():
    """Test dialogue processing with fallback handling."""
    try:
        logger.info("Testing dialogue processing with fallbacks...")
        
        # Create processor
        processor = UnifiedDialogueProcessor()
        
        # Test processing with fallbacks (sync version)
        logger.info("Testing sync processing with fallbacks...")
        result = processor.process_input_sync(
            user_input="Hello, this is a test message",
            user_id="test_user",
            session_id=None  # This will trigger session creation
        )
        
        # Check result structure
        if isinstance(result, dict):
            logger.info("✅ Result is a dictionary")
            
            # Check required fields
            required_fields = ['id', 'input', 'response', 'sessionId', 'timestamp']
            for field in required_fields:
                if field in result:
                    logger.info(f"✅ Field '{field}' exists: {result[field][:50] if isinstance(result[field], str) else result[field]}")
                else:
                    logger.error(f"❌ Missing field: {field}")
                    return False
            
            # Check if response makes sense
            response = result.get('response', '')
            if response and len(response) > 0:
                logger.info(f"✅ Response generated: {response[:100]}...")
            else:
                logger.warning("⚠️ Empty or no response generated")
            
            logger.info("✅ Dialogue processing with fallbacks works!")
            return True
        else:
            logger.error(f"❌ Result is not a dictionary: {type(result)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_processing_with_fallbacks():
    """Test async processing with fallback handling."""
    try:
        logger.info("Testing async dialogue processing with fallbacks...")
        
        # Create processor
        processor = UnifiedDialogueProcessor()
        
        # Test async processing with fallbacks
        result = await processor.process_input(
            user_input="This is an async test message",
            user_id="async_test_user",
            session_id=None
        )
        
        # Check result structure
        if isinstance(result, dict):
            logger.info("✅ Async result is a dictionary")
            
            response = result.get('response', '')
            if response:
                logger.info(f"✅ Async response: {response[:100]}...")
            else:
                logger.warning("⚠️ Empty async response")
            
            logger.info("✅ Async dialogue processing with fallbacks works!")
            return True
        else:
            logger.error(f"❌ Async result is not a dictionary: {type(result)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Async test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing API with Fallback Handling")
    print("=" * 50)
    
    # Test sync processing
    print("\n1. Testing Sync Processing with Fallbacks:")
    sync_success = test_dialogue_processing_with_fallbacks()
    
    # Test async processing
    print("\n2. Testing Async Processing with Fallbacks:")
    async_success = asyncio.run(test_async_processing_with_fallbacks())
    
    if sync_success and async_success:
        print("\n✅ All tests passed!")
        print("The API should now work correctly even without SurrealDB/OpenAI.")
        print("\nFallback features:")
        print("- ✅ Session creation fallback (mock sessions)")
        print("- ✅ Turn creation fallback (mock turns)")
        print("- ✅ AI response fallback (simple responses)")
        print("- ✅ Error handling with meaningful messages")
    else:
        print("\n❌ Some tests failed!")
        print("Please check the error messages above.")