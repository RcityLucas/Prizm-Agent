"""
Unit tests for retriever components.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from langmem.core.models import Memory, MemoryQuery, RetrievedMemory
from langmem.retrievers.base import RetrieverBase, RetrieverError
from langmem.retrievers.vector_retriever import VectorRetriever
from langmem.retrievers.recency_retriever import RecencyRetriever


class TestRetrieverBase:
    """Test suite for the RetrieverBase abstract class."""
    
    def test_abstract_methods(self):
        """Test that RetrieverBase cannot be instantiated directly."""
        mock_storage = MagicMock()
        with pytest.raises(TypeError):
            RetrieverBase(mock_storage)


class TestVectorRetriever:
    """Test suite for the VectorRetriever class."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage object."""
        storage = AsyncMock()
        
        # Mock vector_search method
        storage.vector_search = AsyncMock(return_value=[
            {
                "memory": Memory(
                    id="test-id-1",
                    content="Memory 1",
                    embedding=[0.1, 0.2, 0.3]
                ),
                "score": 0.1  # Lower distance = higher similarity
            },
            {
                "memory": Memory(
                    id="test-id-2",
                    content="Memory 2",
                    embedding=[0.4, 0.5, 0.6]
                ),
                "score": 0.2
            }
        ])
        
        # Mock query method for fallback
        storage.query = AsyncMock(return_value=[
            Memory(id="test-id-1", content="Memory 1", embedding=[0.1, 0.2, 0.3]),
            Memory(id="test-id-2", content="Memory 2", embedding=[0.4, 0.5, 0.6])
        ])
        
        return storage
    
    @pytest.mark.asyncio
    async def test_retrieve_with_embedding(self, mock_storage):
        """Test retrieving memories with an embedding."""
        retriever = VectorRetriever(mock_storage)
        
        query = MemoryQuery(
            content="test query",
            embedding=[0.7, 0.8, 0.9]
        )
        
        memories = await retriever.retrieve(query, limit=2)
        
        mock_storage.vector_search.assert_called_once_with(
            embedding=[0.7, 0.8, 0.9],
            limit=2,
            filters={}
        )
        
        assert len(memories) == 2
        assert memories[0].memory.id == "test-id-1"
        assert memories[0].memory.content == "Memory 1"
        assert 0 <= memories[0].relevance <= 1  # Relevance should be between 0 and 1
        assert memories[1].memory.id == "test-id-2"
        assert memories[1].memory.content == "Memory 2"
        assert 0 <= memories[1].relevance <= 1
    
    @pytest.mark.asyncio
    async def test_retrieve_without_embedding(self, mock_storage):
        """Test retrieving memories without an embedding."""
        retriever = VectorRetriever(mock_storage)
        
        query = MemoryQuery(
            content="test query",
            embedding=None
        )
        
        memories = await retriever.retrieve(query, limit=2)
        
        # Should fall back to regular query
        mock_storage.query.assert_called_once_with({}, limit=2)
        
        assert len(memories) == 2
        assert memories[0].memory.id == "test-id-1"
        assert memories[0].relevance == 0.5  # Default relevance for non-vector search
        assert memories[1].memory.id == "test-id-2"
        assert memories[1].relevance == 0.5
    
    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, mock_storage):
        """Test retrieving memories with filters."""
        retriever = VectorRetriever(mock_storage)
        
        query = MemoryQuery(
            content="test query",
            embedding=[0.7, 0.8, 0.9],
            filters={"memory_type": "test"}
        )
        
        memories = await retriever.retrieve(query, limit=2)
        
        mock_storage.vector_search.assert_called_once_with(
            embedding=[0.7, 0.8, 0.9],
            limit=2,
            filters={"memory_type": "test"}
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_fallback_to_in_memory(self, mock_storage):
        """Test fallback to in-memory calculation when vector_search raises NotImplementedError."""
        # Make vector_search raise NotImplementedError
        mock_storage.vector_search.side_effect = NotImplementedError("Vector search not supported")
        
        retriever = VectorRetriever(mock_storage)
        
        query = MemoryQuery(
            content="test query",
            embedding=[0.7, 0.8, 0.9]
        )
        
        memories = await retriever.retrieve(query, limit=2)
        
        # Should fall back to regular query
        mock_storage.query.assert_called_once()
        
        assert len(memories) == 2
    
    def test_score_memory(self):
        """Test scoring a memory based on vector similarity."""
        mock_storage = MagicMock()
        retriever = VectorRetriever(mock_storage)
        
        # Create a memory and query with similar embeddings
        memory = Memory(
            content="Test memory",
            embedding=[0.1, 0.2, 0.3]
        )
        
        query = MemoryQuery(
            content="Test query",
            embedding=[0.1, 0.2, 0.3]  # Identical embedding should give perfect score
        )
        
        score = retriever.score_memory(memory, query)
        assert score == 1.0  # Perfect match
        
        # Test with different embeddings
        query2 = MemoryQuery(
            content="Different query",
            embedding=[-0.1, -0.2, -0.3]  # Opposite direction should give low score
        )
        
        score2 = retriever.score_memory(memory, query2)
        assert score2 < 0.5  # Should be a low score
        
        # Test with no embeddings
        memory_no_embedding = Memory(content="No embedding")
        query_no_embedding = MemoryQuery(content="No embedding")
        
        score3 = retriever.score_memory(memory_no_embedding, query_no_embedding)
        assert score3 == 0.0  # No embedding should give zero score


class TestRecencyRetriever:
    """Test suite for the RecencyRetriever class."""
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage object."""
        storage = AsyncMock()
        
        # Create memories with different creation times
        now = datetime.now()
        
        # Memory created 1 day ago
        memory1 = Memory(
            id="test-id-1",
            content="Memory 1",
            created_at=now - timedelta(days=1)
        )
        
        # Memory created 3 days ago
        memory2 = Memory(
            id="test-id-2",
            content="Memory 2",
            created_at=now - timedelta(days=3)
        )
        
        # Memory created 7 days ago
        memory3 = Memory(
            id="test-id-3",
            content="Memory 3",
            created_at=now - timedelta(days=7)
        )
        
        # Mock query method
        storage.query = AsyncMock(return_value=[memory1, memory2, memory3])
        
        return storage
    
    @pytest.mark.asyncio
    async def test_retrieve(self, mock_storage):
        """Test retrieving memories based on recency."""
        retriever = RecencyRetriever(mock_storage, recency_window_days=10, decay_factor=0.1)
        
        query = MemoryQuery(content="test query")
        
        memories = await retriever.retrieve(query, limit=3)
        
        mock_storage.query.assert_called_once()
        
        # Should return memories in order of recency
        assert len(memories) == 3
        assert memories[0].memory.id == "test-id-1"  # Most recent
        assert memories[1].memory.id == "test-id-2"
        assert memories[2].memory.id == "test-id-3"  # Least recent
        
        # Check that relevance scores are in descending order
        assert memories[0].relevance > memories[1].relevance > memories[2].relevance
    
    @pytest.mark.asyncio
    async def test_retrieve_with_window(self, mock_storage):
        """Test retrieving memories with a specific recency window."""
        # Set window to 2 days, which should exclude the 3rd memory (7 days old)
        retriever = RecencyRetriever(mock_storage, recency_window_days=2, decay_factor=0.1)
        
        query = MemoryQuery(content="test query")
        
        # Note: The filtering by date would normally happen in the storage layer,
        # but our mock just returns all memories. In a real implementation,
        # the query to storage would include a date filter.
        memories = await retriever.retrieve(query, limit=3)
        
        mock_storage.query.assert_called_once()
        
        # Should still return all memories because our mock doesn't filter
        assert len(memories) == 3
    
    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self, mock_storage):
        """Test retrieving memories with additional filters."""
        retriever = RecencyRetriever(mock_storage)
        
        query = MemoryQuery(
            content="test query",
            filters={"memory_type": "test"}
        )
        
        await retriever.retrieve(query, limit=3)
        
        # Check that the filters were passed to the storage query
        call_args = mock_storage.query.call_args[0][0]
        assert "memory_type" in call_args
        assert call_args["memory_type"] == "test"
    
    def test_score_memory(self):
        """Test scoring a memory based on recency."""
        mock_storage = MagicMock()
        retriever = RecencyRetriever(mock_storage, decay_factor=0.1)
        
        now = datetime.now()
        
        # Test with a very recent memory (1 hour ago)
        recent_memory = Memory(
            content="Recent memory",
            created_at=now - timedelta(hours=1)
        )
        
        # Test with an older memory (5 days ago)
        old_memory = Memory(
            content="Old memory",
            created_at=now - timedelta(days=5)
        )
        
        query = MemoryQuery(content="Test query")
        
        recent_score = retriever.score_memory(recent_memory, query)
        old_score = retriever.score_memory(old_memory, query)
        
        # Recent memory should have a higher score
        assert recent_score > old_score
        
        # Recent memory should have a score close to 1
        assert recent_score > 0.9
        
        # Old memory should have a lower score but still positive
        assert 0 < old_score < 0.9
    
    def test_set_recency_window(self):
        """Test setting the recency window."""
        mock_storage = MagicMock()
        retriever = RecencyRetriever(mock_storage, recency_window_days=7)
        
        assert retriever.recency_window_days == 7
        
        retriever.set_recency_window(14)
        assert retriever.recency_window_days == 14
    
    def test_set_decay_factor(self):
        """Test setting the decay factor."""
        mock_storage = MagicMock()
        retriever = RecencyRetriever(mock_storage, decay_factor=0.1)
        
        assert retriever.decay_factor == 0.1
        
        retriever.set_decay_factor(0.2)
        assert retriever.decay_factor == 0.2
