"""
Unit tests for the MemoryManager class.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.core.memory_manager import MemoryManager


class TestMemoryManager:
    """Test suite for the MemoryManager class."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage object."""
        storage = AsyncMock()
        storage.create = AsyncMock(return_value="test-id-123")
        storage.get = AsyncMock(return_value=Memory(id="test-id-123", content="Test memory"))
        storage.update = AsyncMock(return_value=True)
        storage.delete = AsyncMock(return_value=True)
        storage.query = AsyncMock(return_value=[
            Memory(id="test-id-1", content="Memory 1"),
            Memory(id="test-id-2", content="Memory 2")
        ])
        return storage
    
    @pytest.fixture
    def mock_retriever(self):
        """Create a mock retriever object."""
        retriever = AsyncMock()
        retriever.retrieve = AsyncMock(return_value=[
            RetrievedMemory(
                memory=Memory(id="test-id-1", content="Memory 1"),
                relevance=0.9
            ),
            RetrievedMemory(
                memory=Memory(id="test-id-2", content="Memory 2"),
                relevance=0.7
            )
        ])
        return retriever
    
    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        provider = MagicMock()
        provider.get_embedding = MagicMock(return_value=[0.1, 0.2, 0.3])
        return provider
    
    @pytest.mark.asyncio
    async def test_add_memory(self, mock_storage, mock_retriever, mock_embedding_provider):
        """Test adding a memory."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever,
            embedding_provider=mock_embedding_provider
        )
        
        memory_id = await manager.add_memory(
            content="Test memory content",
            memory_type="test",
            metadata={"source": "test"}
        )
        
        assert memory_id == "test-id-123"
        mock_embedding_provider.get_embedding.assert_called_once_with("Test memory content")
        mock_storage.create.assert_called_once()
        
        # Check that the memory object passed to create has the expected values
        created_memory = mock_storage.create.call_args[0][0]
        assert created_memory.content == "Test memory content"
        assert created_memory.memory_type == "test"
        assert created_memory.metadata == {"source": "test"}
        assert created_memory.embedding == [0.1, 0.2, 0.3]
    
    @pytest.mark.asyncio
    async def test_add_memory_with_embedding(self, mock_storage, mock_retriever):
        """Test adding a memory with a pre-computed embedding."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever,
            embedding_provider=None  # No embedding provider
        )
        
        embedding = [0.4, 0.5, 0.6]
        memory_id = await manager.add_memory(
            content="Test memory content",
            embedding=embedding
        )
        
        assert memory_id == "test-id-123"
        mock_storage.create.assert_called_once()
        
        # Check that the memory object passed to create has the expected embedding
        created_memory = mock_storage.create.call_args[0][0]
        assert created_memory.embedding == embedding
    
    @pytest.mark.asyncio
    async def test_add_memory_no_embedding(self, mock_storage, mock_retriever):
        """Test adding a memory without an embedding and no provider."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever,
            embedding_provider=None  # No embedding provider
        )
        
        memory_id = await manager.add_memory(content="Test memory content")
        
        assert memory_id == "test-id-123"
        mock_storage.create.assert_called_once()
        
        # Check that the memory object passed to create has an empty embedding
        created_memory = mock_storage.create.call_args[0][0]
        assert created_memory.embedding == []
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_string_query(self, mock_storage, mock_retriever, mock_embedding_provider):
        """Test retrieving memories with a string query."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever,
            embedding_provider=mock_embedding_provider
        )
        
        memories = await manager.retrieve_memories("test query")
        
        mock_embedding_provider.get_embedding.assert_called_once_with("test query")
        mock_retriever.retrieve.assert_called_once()
        
        # Check that the query object passed to retrieve has the expected values
        query = mock_retriever.retrieve.call_args[0][0]
        assert query.content == "test query"
        assert query.embedding == [0.1, 0.2, 0.3]
        
        # Check the returned memories
        assert len(memories) == 2
        assert memories[0].memory.id == "test-id-1"
        assert memories[0].relevance == 0.9
        assert memories[1].memory.id == "test-id-2"
        assert memories[1].relevance == 0.7
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_query_object(self, mock_storage, mock_retriever):
        """Test retrieving memories with a MemoryQuery object."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever,
            embedding_provider=None
        )
        
        query = MemoryQuery(
            content="test query",
            embedding=[0.7, 0.8, 0.9],
            filters={"memory_type": "test"}
        )
        
        memories = await manager.retrieve_memories(query)
        
        mock_retriever.retrieve.assert_called_once()
        
        # Check that the query object passed to retrieve is the same one
        passed_query = mock_retriever.retrieve.call_args[0][0]
        assert passed_query is query
        
        # Check the returned memories
        assert len(memories) == 2
    
    @pytest.mark.asyncio
    async def test_get_memory(self, mock_storage, mock_retriever):
        """Test getting a memory by ID."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever
        )
        
        memory = await manager.get_memory("test-id-123")
        
        mock_storage.get.assert_called_once_with("test-id-123")
        assert memory.id == "test-id-123"
        assert memory.content == "Test memory"
    
    @pytest.mark.asyncio
    async def test_update_memory(self, mock_storage, mock_retriever, mock_embedding_provider):
        """Test updating a memory."""
        # Setup the mock to return a specific memory
        original_memory = Memory(
            id="test-id-123",
            content="Original content",
            embedding=[0.1, 0.2, 0.3]
        )
        mock_storage.get.return_value = original_memory
        
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever,
            embedding_provider=mock_embedding_provider
        )
        
        # Create an updated memory with the same ID but different content
        updated_memory = Memory(
            id="test-id-123",
            content="Updated content",
            embedding=None  # Should be regenerated
        )
        
        success = await manager.update_memory(updated_memory)
        
        assert success is True
        mock_storage.get.assert_called_once_with("test-id-123")
        mock_embedding_provider.get_embedding.assert_called_once_with("Updated content")
        mock_storage.update.assert_called_once()
        
        # Check that the memory object passed to update has the regenerated embedding
        updated_memory = mock_storage.update.call_args[0][0]
        assert updated_memory.embedding == [0.1, 0.2, 0.3]  # From the mock embedding provider
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, mock_storage, mock_retriever):
        """Test deleting a memory."""
        manager = MemoryManager(
            storage=mock_storage,
            retriever=mock_retriever
        )
        
        success = await manager.delete_memory("test-id-123")
        
        assert success is True
        mock_storage.delete.assert_called_once_with("test-id-123")
