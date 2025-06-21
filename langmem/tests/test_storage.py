"""
Unit tests for storage components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from langmem.core.models import Memory
from langmem.storage.base import StorageBase, StorageError
from langmem.storage.surreal_adapter import SurrealAdapter


class TestStorageBase:
    """Test suite for the StorageBase abstract class."""
    
    def test_abstract_methods(self):
        """Test that StorageBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            StorageBase()


class TestSurrealAdapter:
    """Test suite for the SurrealAdapter class."""
    
    @pytest.fixture
    def mock_surreal_client(self):
        """Create a mock SurrealDB client."""
        with patch('langmem.storage.surreal_adapter.Surreal') as mock_surreal:
            client = AsyncMock()
            mock_surreal.return_value = client
            
            # Mock the connect method
            client.connect = AsyncMock()
            
            # Mock the use method
            client.use = AsyncMock()
            
            # Mock the signin method
            client.signin = AsyncMock()
            
            # Mock the query method
            client.query = AsyncMock(return_value={"result": [[]]})
            
            # Mock the create method
            client.create = AsyncMock(return_value=[{"id": "memories:test-id-123"}])
            
            # Mock the select method
            client.select = AsyncMock(return_value={
                "id": "memories:test-id-123",
                "content": "Test memory",
                "embedding": [0.1, 0.2, 0.3],
                "memory_type": "test",
                "created_at": "2023-01-01T12:00:00Z",
                "metadata": {"source": "test"}
            })
            
            # Mock the update method
            client.update = AsyncMock(return_value=[{"id": "memories:test-id-123"}])
            
            # Mock the delete method
            client.delete = AsyncMock(return_value=True)
            
            yield client
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_surreal_client):
        """Test connecting to SurrealDB."""
        adapter = SurrealAdapter(
            url="ws://localhost:8000/rpc",
            namespace="test",
            database="test",
            username="user",
            password="pass"
        )
        
        await adapter.connect()
        
        mock_surreal_client.connect.assert_called_once()
        mock_surreal_client.use.assert_called_once_with("test", "test")
        mock_surreal_client.signin.assert_called_once_with({"user": "user", "pass": "pass"})
        mock_surreal_client.query.assert_called()  # For table structure
    
    @pytest.mark.asyncio
    async def test_create(self, mock_surreal_client):
        """Test creating a memory in SurrealDB."""
        adapter = SurrealAdapter()
        adapter.client = mock_surreal_client  # Skip connect
        
        memory = Memory(
            content="Test memory",
            embedding=[0.1, 0.2, 0.3],
            memory_type="test",
            metadata={"source": "test"}
        )
        
        memory_id = await adapter.create(memory)
        
        assert memory_id == "test-id-123"
        mock_surreal_client.create.assert_called_once()
        
        # Check that the memory dict passed to create has the expected values
        created_memory = mock_surreal_client.create.call_args[0][1]
        assert created_memory["content"] == "Test memory"
        assert created_memory["embedding"] == [0.1, 0.2, 0.3]
        assert created_memory["memory_type"] == "test"
        assert created_memory["metadata"] == {"source": "test"}
    
    @pytest.mark.asyncio
    async def test_get(self, mock_surreal_client):
        """Test getting a memory from SurrealDB."""
        adapter = SurrealAdapter()
        adapter.client = mock_surreal_client  # Skip connect
        
        memory = await adapter.get("test-id-123")
        
        mock_surreal_client.select.assert_called_once_with("memories:test-id-123")
        assert memory.id == "test-id-123"
        assert memory.content == "Test memory"
        assert memory.embedding == [0.1, 0.2, 0.3]
        assert memory.memory_type == "test"
        assert memory.metadata == {"source": "test"}
    
    @pytest.mark.asyncio
    async def test_update(self, mock_surreal_client):
        """Test updating a memory in SurrealDB."""
        adapter = SurrealAdapter()
        adapter.client = mock_surreal_client  # Skip connect
        
        memory = Memory(
            id="test-id-123",
            content="Updated memory",
            embedding=[0.4, 0.5, 0.6],
            memory_type="updated",
            metadata={"source": "update-test"}
        )
        
        success = await adapter.update(memory)
        
        assert success is True
        mock_surreal_client.update.assert_called_once()
        
        # Check that the memory dict passed to update has the expected values
        updated_memory = mock_surreal_client.update.call_args[0][1]
        assert updated_memory["content"] == "Updated memory"
        assert updated_memory["embedding"] == [0.4, 0.5, 0.6]
        assert updated_memory["memory_type"] == "updated"
        assert updated_memory["metadata"] == {"source": "update-test"}
    
    @pytest.mark.asyncio
    async def test_delete(self, mock_surreal_client):
        """Test deleting a memory from SurrealDB."""
        adapter = SurrealAdapter()
        adapter.client = mock_surreal_client  # Skip connect
        
        success = await adapter.delete("test-id-123")
        
        assert success is True
        mock_surreal_client.delete.assert_called_once_with("memories:test-id-123")
    
    @pytest.mark.asyncio
    async def test_query(self, mock_surreal_client):
        """Test querying memories from SurrealDB."""
        # Setup the mock to return some memories
        mock_surreal_client.query.return_value = {
            "result": [[
                {
                    "id": "memories:test-id-1",
                    "content": "Memory 1",
                    "embedding": [0.1, 0.2, 0.3],
                    "memory_type": "test",
                    "created_at": "2023-01-01T12:00:00Z",
                    "metadata": {"source": "test"}
                },
                {
                    "id": "memories:test-id-2",
                    "content": "Memory 2",
                    "embedding": [0.4, 0.5, 0.6],
                    "memory_type": "test",
                    "created_at": "2023-01-02T12:00:00Z",
                    "metadata": {"source": "test"}
                }
            ]]
        }
        
        adapter = SurrealAdapter()
        adapter.client = mock_surreal_client  # Skip connect
        
        memories = await adapter.query({"memory_type": "test"}, limit=10)
        
        mock_surreal_client.query.assert_called()
        assert len(memories) == 2
        assert memories[0].id == "test-id-1"
        assert memories[0].content == "Memory 1"
        assert memories[1].id == "test-id-2"
        assert memories[1].content == "Memory 2"
    
    @pytest.mark.asyncio
    async def test_vector_search(self, mock_surreal_client):
        """Test vector search in SurrealDB."""
        # Setup the mock to return some memories with scores
        mock_surreal_client.query.return_value = {
            "result": [[
                {
                    "id": "memories:test-id-1",
                    "content": "Memory 1",
                    "embedding": [0.1, 0.2, 0.3],
                    "memory_type": "test",
                    "created_at": "2023-01-01T12:00:00Z",
                    "metadata": {"source": "test"},
                    "score": 0.1  # Lower distance = higher similarity
                },
                {
                    "id": "memories:test-id-2",
                    "content": "Memory 2",
                    "embedding": [0.4, 0.5, 0.6],
                    "memory_type": "test",
                    "created_at": "2023-01-02T12:00:00Z",
                    "metadata": {"source": "test"},
                    "score": 0.2
                }
            ]]
        }
        
        adapter = SurrealAdapter()
        adapter.client = mock_surreal_client  # Skip connect
        
        results = await adapter.vector_search(
            embedding=[0.1, 0.2, 0.3],
            limit=10,
            filters={"memory_type": "test"}
        )
        
        mock_surreal_client.query.assert_called()
        assert len(results) == 2
        
        # Check the first result
        assert results[0]["memory"].id == "test-id-1"
        assert results[0]["memory"].content == "Memory 1"
        assert results[0]["score"] == 0.1
        
        # Check the second result
        assert results[1]["memory"].id == "test-id-2"
        assert results[1]["memory"].content == "Memory 2"
        assert results[1]["score"] == 0.2
