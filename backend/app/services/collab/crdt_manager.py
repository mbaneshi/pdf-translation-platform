# CRDT state manager for real-time collaboration
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
import logging

from .snapshot_store import SnapshotStore
from .models import CollabMessage, UserInfo

logger = logging.getLogger(__name__)


class CRDTStateManager:
    """Manages CRDT state for real-time collaboration"""
    
    def __init__(self):
        self.snapshot_store = SnapshotStore()
        self.active_states: Dict[int, Dict[str, Any]] = {}  # page_id -> state
        self.operation_logs: Dict[int, List[Dict[str, Any]]] = {}  # page_id -> operations
        self.presence: Dict[int, Set[str]] = {}  # page_id -> user_ids
        self.locks: Dict[int, Dict[str, Any]] = {}  # page_id -> lock_info
    
    async def initialize_page_state(self, page_id: int) -> Dict[str, Any]:
        """Initialize or restore state for a page"""
        try:
            # Try to restore from latest snapshot
            latest_snapshot = await self.snapshot_store.get_latest_snapshot(page_id)
            
            if latest_snapshot:
                state = latest_snapshot["state"]
                logger.info(f"Restored state for page {page_id} from snapshot")
            else:
                # Initialize empty state
                state = {
                    "page_id": page_id,
                    "version": 1,
                    "segments": [],
                    "comments": [],
                    "suggestions": [],
                    "metadata": {
                        "created_at": datetime.utcnow().isoformat(),
                        "last_modified": datetime.utcnow().isoformat(),
                        "last_modified_by": None
                    }
                }
                logger.info(f"Initialized new state for page {page_id}")
            
            self.active_states[page_id] = state
            self.operation_logs[page_id] = []
            self.presence[page_id] = set()
            
            return state
            
        except Exception as e:
            logger.error(f"Error initializing page state: {e}")
            return {}
    
    async def apply_operation(
        self, 
        page_id: int, 
        operation: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """Apply a CRDT operation to the page state"""
        try:
            if page_id not in self.active_states:
                await self.initialize_page_state(page_id)
            
            state = self.active_states[page_id]
            operation_id = str(uuid.uuid4())
            
            # Add operation metadata
            operation["id"] = operation_id
            operation["timestamp"] = datetime.utcnow().isoformat()
            operation["user_id"] = user_id
            
            # Apply operation based on type
            result = await self._apply_operation_to_state(state, operation)
            
            # Log the operation
            self.operation_logs[page_id].append(operation)
            
            # Update state metadata
            state["version"] += 1
            state["metadata"]["last_modified"] = datetime.utcnow().isoformat()
            state["metadata"]["last_modified_by"] = user_id
            
            # Create snapshot periodically
            if state["version"] % 10 == 0:  # Every 10 operations
                await self.snapshot_store.create_snapshot(
                    page_id, state, user_id, state["version"]
                )
            
            return {
                "operation_id": operation_id,
                "success": True,
                "new_version": state["version"],
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error applying operation: {e}")
            return {
                "operation_id": operation.get("id", ""),
                "success": False,
                "error": str(e)
            }
    
    async def _apply_operation_to_state(
        self, 
        state: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a specific operation to the state"""
        op_type = operation.get("type")
        
        if op_type == "insert_segment":
            return await self._insert_segment(state, operation)
        elif op_type == "update_segment":
            return await self._update_segment(state, operation)
        elif op_type == "delete_segment":
            return await self._delete_segment(state, operation)
        elif op_type == "add_comment":
            return await self._add_comment(state, operation)
        elif op_type == "update_comment":
            return await self._update_comment(state, operation)
        elif op_type == "delete_comment":
            return await self._delete_comment(state, operation)
        elif op_type == "add_suggestion":
            return await self._add_suggestion(state, operation)
        elif op_type == "accept_suggestion":
            return await self._accept_suggestion(state, operation)
        elif op_type == "reject_suggestion":
            return await self._reject_suggestion(state, operation)
        else:
            raise ValueError(f"Unknown operation type: {op_type}")
    
    async def _insert_segment(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new segment"""
        segment = {
            "id": operation.get("segment_id", str(uuid.uuid4())),
            "text": operation.get("text", ""),
            "position": operation.get("position", 0),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": operation.get("user_id"),
            "version": 1
        }
        
        state["segments"].append(segment)
        return {"segment_id": segment["id"], "position": segment["position"]}
    
    async def _update_segment(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing segment"""
        segment_id = operation.get("segment_id")
        new_text = operation.get("text", "")
        
        for segment in state["segments"]:
            if segment["id"] == segment_id:
                segment["text"] = new_text
                segment["version"] += 1
                segment["last_modified"] = datetime.utcnow().isoformat()
                segment["last_modified_by"] = operation.get("user_id")
                return {"segment_id": segment_id, "updated": True}
        
        raise ValueError(f"Segment {segment_id} not found")
    
    async def _delete_segment(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a segment"""
        segment_id = operation.get("segment_id")
        
        for i, segment in enumerate(state["segments"]):
            if segment["id"] == segment_id:
                del state["segments"][i]
                return {"segment_id": segment_id, "deleted": True}
        
        raise ValueError(f"Segment {segment_id} not found")
    
    async def _add_comment(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Add a comment"""
        comment = {
            "id": operation.get("comment_id", str(uuid.uuid4())),
            "segment_id": operation.get("segment_id"),
            "text": operation.get("text", ""),
            "author_id": operation.get("user_id"),
            "created_at": datetime.utcnow().isoformat(),
            "resolved": False
        }
        
        state["comments"].append(comment)
        return {"comment_id": comment["id"]}
    
    async def _update_comment(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Update a comment"""
        comment_id = operation.get("comment_id")
        new_text = operation.get("text", "")
        
        for comment in state["comments"]:
            if comment["id"] == comment_id:
                comment["text"] = new_text
                comment["last_modified"] = datetime.utcnow().isoformat()
                return {"comment_id": comment_id, "updated": True}
        
        raise ValueError(f"Comment {comment_id} not found")
    
    async def _delete_comment(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a comment"""
        comment_id = operation.get("comment_id")
        
        for i, comment in enumerate(state["comments"]):
            if comment["id"] == comment_id:
                del state["comments"][i]
                return {"comment_id": comment_id, "deleted": True}
        
        raise ValueError(f"Comment {comment_id} not found")
    
    async def _add_suggestion(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Add a suggestion"""
        suggestion = {
            "id": operation.get("suggestion_id", str(uuid.uuid4())),
            "segment_id": operation.get("segment_id"),
            "original_text": operation.get("original_text", ""),
            "suggested_text": operation.get("suggested_text", ""),
            "author_id": operation.get("user_id"),
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        state["suggestions"].append(suggestion)
        return {"suggestion_id": suggestion["id"]}
    
    async def _accept_suggestion(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Accept a suggestion"""
        suggestion_id = operation.get("suggestion_id")
        
        for suggestion in state["suggestions"]:
            if suggestion["id"] == suggestion_id:
                suggestion["status"] = "accepted"
                suggestion["accepted_at"] = datetime.utcnow().isoformat()
                suggestion["accepted_by"] = operation.get("user_id")
                return {"suggestion_id": suggestion_id, "accepted": True}
        
        raise ValueError(f"Suggestion {suggestion_id} not found")
    
    async def _reject_suggestion(self, state: Dict[str, Any], operation: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a suggestion"""
        suggestion_id = operation.get("suggestion_id")
        
        for suggestion in state["suggestions"]:
            if suggestion["id"] == suggestion_id:
                suggestion["status"] = "rejected"
                suggestion["rejected_at"] = datetime.utcnow().isoformat()
                suggestion["rejected_by"] = operation.get("user_id")
                return {"suggestion_id": suggestion_id, "rejected": True}
        
        raise ValueError(f"Suggestion {suggestion_id} not found")
    
    async def get_page_state(self, page_id: int) -> Optional[Dict[str, Any]]:
        """Get current state for a page"""
        if page_id not in self.active_states:
            await self.initialize_page_state(page_id)
        
        return self.active_states.get(page_id)
    
    async def get_operation_history(
        self, 
        page_id: int, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get operation history for a page"""
        operations = self.operation_logs.get(page_id, [])
        return operations[offset:offset + limit]
    
    async def create_snapshot(self, page_id: int, user_id: str) -> str:
        """Create a snapshot of the current state"""
        try:
            state = await self.get_page_state(page_id)
            if not state:
                raise ValueError(f"No state found for page {page_id}")
            
            snapshot_id = await self.snapshot_store.create_snapshot(
                page_id, state, user_id, state["version"]
            )
            
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            raise
    
    async def restore_from_snapshot(self, page_id: int, snapshot_id: str) -> bool:
        """Restore page state from a snapshot"""
        try:
            snapshot = await self.snapshot_store.get_snapshot(snapshot_id)
            if not snapshot:
                return False
            
            self.active_states[page_id] = snapshot["state"]
            self.operation_logs[page_id] = []
            
            logger.info(f"Restored page {page_id} from snapshot {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from snapshot: {e}")
            return False
    
    async def update_presence(self, page_id: int, user_id: str, action: str) -> Set[str]:
        """Update user presence for a page"""
        if page_id not in self.presence:
            self.presence[page_id] = set()
        
        if action == "join":
            self.presence[page_id].add(user_id)
        elif action == "leave":
            self.presence[page_id].discard(user_id)
        
        return self.presence[page_id].copy()
    
    async def get_presence(self, page_id: int) -> Set[str]:
        """Get current presence for a page"""
        return self.presence.get(page_id, set()).copy()
    
    async def acquire_lock(self, page_id: int, user_id: str, resource: str) -> bool:
        """Acquire a lock on a resource"""
        if page_id not in self.locks:
            self.locks[page_id] = {}
        
        lock_key = f"{resource}"
        current_lock = self.locks[page_id].get(lock_key)
        
        if current_lock and current_lock["user_id"] != user_id:
            return False  # Lock held by another user
        
        self.locks[page_id][lock_key] = {
            "user_id": user_id,
            "acquired_at": datetime.utcnow().isoformat(),
            "resource": resource
        }
        
        return True
    
    async def release_lock(self, page_id: int, user_id: str, resource: str) -> bool:
        """Release a lock on a resource"""
        if page_id not in self.locks:
            return False
        
        lock_key = f"{resource}"
        current_lock = self.locks[page_id].get(lock_key)
        
        if current_lock and current_lock["user_id"] == user_id:
            del self.locks[page_id][lock_key]
            return True
        
        return False
    
    async def get_locks(self, page_id: int) -> Dict[str, Any]:
        """Get current locks for a page"""
        return self.locks.get(page_id, {}).copy()
    
    async def cleanup_page_state(self, page_id: int):
        """Clean up state for a page (called when no users are present)"""
        try:
            # Create final snapshot
            if page_id in self.active_states:
                await self.snapshot_store.create_snapshot(
                    page_id, 
                    self.active_states[page_id], 
                    "system", 
                    self.active_states[page_id]["version"]
                )
            
            # Clean up active state
            self.active_states.pop(page_id, None)
            self.operation_logs.pop(page_id, None)
            self.presence.pop(page_id, None)
            self.locks.pop(page_id, None)
            
            logger.info(f"Cleaned up state for page {page_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up page state: {e}")
