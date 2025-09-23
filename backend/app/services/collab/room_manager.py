# Room manager for collaboration service
import json
import uuid
import asyncio
from typing import Dict, Set, List, Optional
from datetime import datetime, timedelta
from fastapi import WebSocket
import logging

from .models import (
    CollaborationMessage, PresenceData, OperationData, 
    CommentData, SuggestionData, RoomState, SnapshotData
)

logger = logging.getLogger(__name__)


class RoomManager:
    """Manages collaboration rooms and WebSocket connections"""
    
    def __init__(self):
        # Room state: page_id -> set of websockets
        self.rooms: Dict[int, Set[WebSocket]] = {}
        
        # User presence: page_id -> websocket -> presence_data
        self.presence: Dict[int, Dict[WebSocket, PresenceData]] = {}
        
        # Room state data: page_id -> room_state
        self.room_states: Dict[int, RoomState] = {}
        
        # Snapshots: page_id -> list of snapshots
        self.snapshots: Dict[int, List[SnapshotData]] = {}
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_rooms())
    
    async def _cleanup_rooms(self):
        """Background task to clean up stale rooms and presence data"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                current_time = datetime.utcnow()
                stale_threshold = timedelta(minutes=5)
                
                # Clean up stale presence data
                for page_id, presence_dict in list(self.presence.items()):
                    stale_websockets = []
                    for websocket, presence in presence_dict.items():
                        if presence.last_seen:
                            last_seen = datetime.fromisoformat(presence.last_seen)
                            if current_time - last_seen > stale_threshold:
                                stale_websockets.append(websocket)
                    
                    for websocket in stale_websockets:
                        await self.disconnect(page_id, websocket)
                
                # Clean up empty rooms
                empty_rooms = [
                    page_id for page_id, websockets in self.rooms.items()
                    if not websockets
                ]
                for page_id in empty_rooms:
                    self._cleanup_room(page_id)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def _cleanup_room(self, page_id: int):
        """Clean up room data when empty"""
        if page_id in self.rooms:
            del self.rooms[page_id]
        if page_id in self.presence:
            del self.presence[page_id]
        # Keep room states and snapshots for potential reconnection
    
    async def connect(self, page_id: int, websocket: WebSocket):
        """Add a WebSocket connection to a room"""
        if page_id not in self.rooms:
            self.rooms[page_id] = set()
            self.presence[page_id] = {}
            self.room_states[page_id] = RoomState(
                page_id=page_id,
                participants=[],
                operations=[],
                comments=[],
                suggestions=[],
                last_updated=datetime.utcnow().isoformat()
            )
        
        self.rooms[page_id].add(websocket)
        
        # Initialize presence data
        presence = PresenceData(
            user_id=str(uuid.uuid4()),
            username="Anonymous",
            role="viewer",
            last_seen=datetime.utcnow().isoformat()
        )
        self.presence[page_id][websocket] = presence
        
        # Update room state
        await self._update_room_state(page_id)
        
        # Notify other participants
        await self._broadcast_presence_update(page_id, websocket, presence)
    
    async def disconnect(self, page_id: int, websocket: WebSocket):
        """Remove a WebSocket connection from a room"""
        if page_id in self.rooms and websocket in self.rooms[page_id]:
            self.rooms[page_id].remove(websocket)
            
            # Remove presence data
            if page_id in self.presence and websocket in self.presence[page_id]:
                del self.presence[page_id][websocket]
            
            # Update room state
            await self._update_room_state(page_id)
            
            # Notify other participants
            await self._broadcast_presence_leave(page_id, websocket)
            
            # Clean up empty room
            if not self.rooms[page_id]:
                self._cleanup_room(page_id)
    
    async def update_presence(
        self, 
        page_id: int, 
        websocket: WebSocket, 
        presence_data: Dict
    ):
        """Update user presence in a room"""
        if page_id not in self.presence or websocket not in self.presence[page_id]:
            return
        
        current_presence = self.presence[page_id][websocket]
        
        # Update presence data
        if "cursor_position" in presence_data:
            current_presence.cursor_position = presence_data["cursor_position"]
        if "selection_range" in presence_data:
            current_presence.selection_range = presence_data["selection_range"]
        if "is_typing" in presence_data:
            current_presence.is_typing = presence_data["is_typing"]
        if "username" in presence_data:
            current_presence.username = presence_data["username"]
        if "role" in presence_data:
            current_presence.role = presence_data["role"]
        
        current_presence.last_seen = datetime.utcnow().isoformat()
        
        # Update room state
        await self._update_room_state(page_id)
        
        # Broadcast presence update
        await self._broadcast_presence_update(page_id, websocket, current_presence)
    
    async def broadcast_operation(
        self, 
        page_id: int, 
        sender_websocket: WebSocket, 
        operation_data: Dict
    ):
        """Broadcast a CRDT operation to all participants except sender"""
        if page_id not in self.rooms:
            return
        
        # Create operation
        operation = OperationData(
            operation_id=str(uuid.uuid4()),
            operation_type=operation_data.get("type", "unknown"),
            position=operation_data.get("position", 0),
            content=operation_data.get("content"),
            attributes=operation_data.get("attributes"),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Add to room state
        if page_id in self.room_states:
            self.room_states[page_id].operations.append(operation)
            self.room_states[page_id].last_updated = datetime.utcnow().isoformat()
        
        # Broadcast to other participants
        message = CollaborationMessage(
            type="operation",
            data=operation.to_dict(),
            timestamp=datetime.utcnow().isoformat(),
            page_id=page_id
        )
        
        await self._broadcast_to_room_except(page_id, sender_websocket, message)
    
    async def broadcast_comment(
        self, 
        page_id: int, 
        sender_websocket: WebSocket, 
        comment_data: Dict
    ):
        """Broadcast a comment to all participants"""
        if page_id not in self.rooms:
            return
        
        # Create comment
        comment = CommentData(
            comment_id=str(uuid.uuid4()),
            segment_id=comment_data.get("segment_id", ""),
            content=comment_data.get("content", ""),
            author_id=comment_data.get("author_id", "anonymous"),
            author_name=comment_data.get("author_name", "Anonymous"),
            status=comment_data.get("status", "open"),
            created_at=datetime.utcnow().isoformat()
        )
        
        # Add to room state
        if page_id in self.room_states:
            self.room_states[page_id].comments.append(comment)
            self.room_states[page_id].last_updated = datetime.utcnow().isoformat()
        
        # Broadcast to all participants
        message = CollaborationMessage(
            type="comment",
            data=comment.to_dict(),
            timestamp=datetime.utcnow().isoformat(),
            page_id=page_id
        )
        
        await self._broadcast_to_room(page_id, message)
    
    async def broadcast_suggestion(
        self, 
        page_id: int, 
        sender_websocket: WebSocket, 
        suggestion_data: Dict
    ):
        """Broadcast a suggestion to all participants"""
        if page_id not in self.rooms:
            return
        
        # Create suggestion
        suggestion = SuggestionData(
            suggestion_id=str(uuid.uuid4()),
            segment_id=suggestion_data.get("segment_id", ""),
            original_text=suggestion_data.get("original_text", ""),
            suggested_text=suggestion_data.get("suggested_text", ""),
            author_id=suggestion_data.get("author_id", "anonymous"),
            author_name=suggestion_data.get("author_name", "Anonymous"),
            confidence=suggestion_data.get("confidence", 0.0),
            status=suggestion_data.get("status", "pending"),
            created_at=datetime.utcnow().isoformat()
        )
        
        # Add to room state
        if page_id in self.room_states:
            self.room_states[page_id].suggestions.append(suggestion)
            self.room_states[page_id].last_updated = datetime.utcnow().isoformat()
        
        # Broadcast to all participants
        message = CollaborationMessage(
            type="suggestion",
            data=suggestion.to_dict(),
            timestamp=datetime.utcnow().isoformat(),
            page_id=page_id
        )
        
        await self._broadcast_to_room(page_id, message)
    
    async def broadcast_to_room(self, page_id: int, message: CollaborationMessage):
        """Broadcast a message to all participants in a room"""
        await self._broadcast_to_room(page_id, message)
    
    async def _broadcast_to_room(self, page_id: int, message: CollaborationMessage):
        """Internal method to broadcast to all participants"""
        if page_id not in self.rooms:
            return
        
        message_text = json.dumps(message.to_dict())
        disconnected = []
        
        for websocket in list(self.rooms[page_id]):
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(page_id, websocket)
    
    async def _broadcast_to_room_except(
        self, 
        page_id: int, 
        exclude_websocket: WebSocket, 
        message: CollaborationMessage
    ):
        """Broadcast to all participants except one"""
        if page_id not in self.rooms:
            return
        
        message_text = json.dumps(message.to_dict())
        disconnected = []
        
        for websocket in list(self.rooms[page_id]):
            if websocket != exclude_websocket:
                try:
                    await websocket.send_text(message_text)
                except Exception as e:
                    logger.warning(f"Failed to send message to websocket: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(page_id, websocket)
    
    async def _broadcast_presence_update(
        self, 
        page_id: int, 
        websocket: WebSocket, 
        presence: PresenceData
    ):
        """Broadcast presence update to other participants"""
        message = CollaborationMessage(
            type="presence_update",
            data=presence.to_dict(),
            timestamp=datetime.utcnow().isoformat(),
            page_id=page_id
        )
        
        await self._broadcast_to_room_except(page_id, websocket, message)
    
    async def _broadcast_presence_leave(self, page_id: int, websocket: WebSocket):
        """Broadcast presence leave to other participants"""
        message = CollaborationMessage(
            type="presence_leave",
            data={"user_id": str(uuid.uuid4())},  # Placeholder
            timestamp=datetime.utcnow().isoformat(),
            page_id=page_id
        )
        
        await self._broadcast_to_room_except(page_id, websocket, message)
    
    async def _update_room_state(self, page_id: int):
        """Update room state with current presence data"""
        if page_id not in self.room_states:
            return
        
        # Update participants list
        participants = []
        if page_id in self.presence:
            for presence in self.presence[page_id].values():
                participants.append(presence)
        
        self.room_states[page_id].participants = participants
        self.room_states[page_id].last_updated = datetime.utcnow().isoformat()
    
    async def get_room_state(self, page_id: int) -> Dict:
        """Get current room state"""
        if page_id not in self.room_states:
            return {
                "page_id": page_id,
                "participants": [],
                "operations": [],
                "comments": [],
                "suggestions": [],
                "last_updated": datetime.utcnow().isoformat()
            }
        
        return self.room_states[page_id].to_dict()
    
    def get_room_participants(self, page_id: int) -> List[Dict]:
        """Get list of participants in a room"""
        if page_id not in self.presence:
            return []
        
        return [presence.to_dict() for presence in self.presence[page_id].values()]
    
    async def create_snapshot(self, page_id: int) -> str:
        """Create a snapshot of the current room state"""
        if page_id not in self.room_states:
            raise ValueError(f"Room {page_id} not found")
        
        snapshot_id = str(uuid.uuid4())
        snapshot = SnapshotData(
            snapshot_id=snapshot_id,
            page_id=page_id,
            state=self.room_states[page_id],
            created_at=datetime.utcnow().isoformat(),
            created_by="system"
        )
        
        if page_id not in self.snapshots:
            self.snapshots[page_id] = []
        
        self.snapshots[page_id].append(snapshot)
        
        # Keep only last 10 snapshots
        if len(self.snapshots[page_id]) > 10:
            self.snapshots[page_id] = self.snapshots[page_id][-10:]
        
        return snapshot_id
    
    async def get_snapshots(self, page_id: int) -> List[Dict]:
        """Get list of snapshots for a room"""
        if page_id not in self.snapshots:
            return []
        
        return [snapshot.to_dict() for snapshot in self.snapshots[page_id]]
