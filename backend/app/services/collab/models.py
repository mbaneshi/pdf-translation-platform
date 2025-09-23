# Collaboration data models
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Types of collaboration messages"""
    PING = "ping"
    PONG = "pong"
    PRESENCE = "presence"
    OPERATION = "operation"
    COMMENT = "comment"
    SUGGESTION = "suggestion"
    ROOM_STATE = "room_state"
    ERROR = "error"


@dataclass
class CollaborationMessage:
    """Base collaboration message"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    user_id: Optional[str] = None
    page_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PresenceData:
    """User presence information"""
    user_id: str
    username: str
    role: str
    cursor_position: Optional[Dict[str, float]] = None
    selection_range: Optional[Dict[str, Any]] = None
    is_typing: bool = False
    last_seen: str = ""
    color: str = "#3B82F6"  # Default blue color
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OperationData:
    """CRDT operation data"""
    operation_id: str
    operation_type: str  # insert, delete, format, etc.
    position: int
    content: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommentData:
    """Comment data"""
    comment_id: str
    segment_id: str
    content: str
    author_id: str
    author_name: str
    status: str = "open"  # open, resolved, reopened
    created_at: str = ""
    updated_at: str = ""
    replies: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuggestionData:
    """Suggestion data"""
    suggestion_id: str
    segment_id: str
    original_text: str
    suggested_text: str
    author_id: str
    author_name: str
    confidence: float = 0.0
    status: str = "pending"  # pending, accepted, rejected
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomState:
    """Room state information"""
    page_id: int
    participants: List[PresenceData]
    operations: List[OperationData]
    comments: List[CommentData]
    suggestions: List[SuggestionData]
    last_updated: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_id": self.page_id,
            "participants": [p.to_dict() for p in self.participants],
            "operations": [o.to_dict() for o in self.operations],
            "comments": [c.to_dict() for c in self.comments],
            "suggestions": [s.to_dict() for s in self.suggestions],
            "last_updated": self.last_updated
        }


@dataclass
class SnapshotData:
    """Snapshot data for room state"""
    snapshot_id: str
    page_id: int
    state: RoomState
    created_at: str
    created_by: str
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "page_id": self.page_id,
            "state": self.state.to_dict(),
            "created_at": self.created_at,
            "created_by": self.created_by,
            "version": self.version
        }
