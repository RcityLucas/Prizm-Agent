"""
Unit tests for the core data models.
"""

import pytest
from datetime import datetime
from langmem.core.models import Memory, MemoryQuery, RetrievedMemory


def test_memory_creation():
    """Test creating a Memory object with default values."""
    content = "This is a test memory"
    memory = Memory(content=content)
    
    assert memory.content == content
    assert memory.id is None
    assert memory.embedding is None
    assert memory.memory_type == "default"
    assert isinstance(memory.created_at, datetime)
    assert memory.metadata == {}


def test_memory_creation_with_values():
    """Test creating a Memory object with custom values."""
    content = "This is a test memory"
    memory_id = "test-id-123"
    embedding = [0.1, 0.2, 0.3]
    memory_type = "conversation"
    created_at = datetime(2023, 1, 1, 12, 0, 0)
    metadata = {"source": "test", "importance": 0.8}
    
    memory = Memory(
        id=memory_id,
        content=content,
        embedding=embedding,
        memory_type=memory_type,
        created_at=created_at,
        metadata=metadata
    )
    
    assert memory.id == memory_id
    assert memory.content == content
    assert memory.embedding == embedding
    assert memory.memory_type == memory_type
    assert memory.created_at == created_at
    assert memory.metadata == metadata


def test_memory_query_creation():
    """Test creating a MemoryQuery object."""
    content = "What is the capital of France?"
    embedding = [0.4, 0.5, 0.6]
    filters = {"memory_type": "fact"}
    
    query = MemoryQuery(
        content=content,
        embedding=embedding,
        filters=filters
    )
    
    assert query.content == content
    assert query.embedding == embedding
    assert query.filters == filters


def test_retrieved_memory_creation():
    """Test creating a RetrievedMemory object."""
    memory = Memory(content="Paris is the capital of France")
    relevance = 0.95
    
    retrieved = RetrievedMemory(
        memory=memory,
        relevance=relevance
    )
    
    assert retrieved.memory == memory
    assert retrieved.relevance == relevance


def test_memory_serialization():
    """Test that Memory objects can be serialized to and from JSON."""
    memory = Memory(
        id="test-id-123",
        content="This is a test memory",
        embedding=[0.1, 0.2, 0.3],
        memory_type="fact",
        metadata={"source": "test"}
    )
    
    # Convert to JSON
    memory_json = memory.model_dump_json()
    
    # Convert back from JSON
    restored_memory = Memory.model_validate_json(memory_json)
    
    # Check that the restored memory matches the original
    assert restored_memory.id == memory.id
    assert restored_memory.content == memory.content
    assert restored_memory.embedding == memory.embedding
    assert restored_memory.memory_type == memory.memory_type
    assert restored_memory.metadata == memory.metadata
