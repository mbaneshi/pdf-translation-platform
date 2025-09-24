# Collaboration WebSocket endpoints
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List
import json
import logging
from datetime import datetime

from app.services.collab.room_manager import RoomManager
from app.services.collab.crdt_manager import CRDTStateManager
from app.services.presence_service import PresenceService
from app.services.comments_service import CommentsService
from app.core.config import settings
from app.core.database import get_db
from app.models.user_models import User

logger = logging.getLogger(__name__)

router = APIRouter()
rooms = RoomManager()
crdt_manager = CRDTStateManager()
presence_service = PresenceService()


@router.websocket("/{page_id}")
async def collab_websocket(websocket: WebSocket, page_id: int):
    """WebSocket endpoint for real-time collaboration on a page"""
    if not settings.COLLAB_ENABLED:
        logger.warning(f"Collaboration attempted for page {page_id} but COLLAB_ENABLED is false.")
        await websocket.close(code=1008, reason="Collaboration features are disabled.")
        return

    await websocket.accept()
    user_id = f"user_{page_id}_{datetime.utcnow().timestamp()}"  # Mock user ID for now
    
    try:
        # Initialize page state
        await crdt_manager.initialize_page_state(page_id)
        
        # Join presence
        await presence_service.join_page(page_id, user_id, {
            "username": f"User {user_id}",
            "role": "editor",
            "color": "#4ECDC4"
        })
        
        # Connect to room
        await rooms.connect(page_id, websocket)
        logger.info(f"User {user_id} connected to page {page_id}")
        
        # Send initial state
        page_state = await crdt_manager.get_page_state(page_id)
        presence_info = await presence_service.get_page_presence(page_id)
        
        await websocket.send_text(json.dumps({
            "type": "initial_state",
            "data": {
                "page_state": page_state,
                "presence": presence_info,
                "user_id": user_id
            }
        }))
        
        # Broadcast user joined
        await rooms.broadcast(page_id, json.dumps({
            "type": "user_joined",
            "data": {
                "user_id": user_id,
                "presence": presence_info
            }
        }))
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_message(page_id, user_id, websocket, message)
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
                
    except WebSocketDisconnect:
        await handle_disconnect(page_id, user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for page {page_id}: {e}")
        await handle_disconnect(page_id, user_id, websocket)


async def handle_disconnect(page_id: int, user_id: str, websocket: WebSocket):
    """Handle user disconnection"""
    try:
        # Leave presence
        await presence_service.leave_page(page_id, user_id)
        
        # Disconnect from room
        await rooms.disconnect(page_id, websocket)
        
        # Broadcast user left
        presence_info = await presence_service.get_page_presence(page_id)
        await rooms.broadcast(page_id, json.dumps({
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "presence": presence_info
            }
        }))
        
        # Clean up if no users left
        if not presence_info.get("active_users"):
            await crdt_manager.cleanup_page_state(page_id)
        
        logger.info(f"User {user_id} disconnected from page {page_id}")
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {e}")


async def handle_message(page_id: int, user_id: str, websocket: WebSocket, message: Dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    data = message.get("data", {})
    
    try:
        if message_type == "ping":
            # Respond to ping with pong
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        elif message_type == "presence_update":
            # Update user presence
            await presence_service.update_cursor_position(page_id, user_id, data.get("cursor", {}))
            await presence_service.update_selection_range(page_id, user_id, data.get("selection", {}))
            
            # Broadcast presence update
            presence_info = await presence_service.get_page_presence(page_id)
            await rooms.broadcast(page_id, json.dumps({
                "type": "presence_update",
                "data": presence_info
            }))
        
        elif message_type == "operation":
            # Handle CRDT operation
            result = await crdt_manager.apply_operation(page_id, data, user_id)
            
            if result["success"]:
                # Broadcast operation to other users
                await rooms.broadcast(page_id, json.dumps({
                    "type": "operation_applied",
                    "data": {
                        "operation": data,
                        "result": result,
                        "user_id": user_id
                    }
                }))
            else:
                # Send error back to sender
                await websocket.send_text(json.dumps({
                    "type": "operation_failed",
                    "data": result
                }))
        
        elif message_type == "comment":
            # Handle comment operations
            comments_service = CommentsService(None)  # Mock DB for now
            
            if data.get("action") == "create":
                comment = await comments_service.create_comment(
                    page_id, data.get("segment_id", ""), data.get("text", ""), user_id
                )
                
                # Broadcast new comment
                await rooms.broadcast(page_id, json.dumps({
                    "type": "comment_created",
                    "data": comment
                }))
            
            elif data.get("action") == "update":
                result = await comments_service.update_comment(
                    data.get("comment_id", ""), data.get("text", ""), user_id
                )
                
                # Broadcast comment update
                await rooms.broadcast(page_id, json.dumps({
                    "type": "comment_updated",
                    "data": result
                }))
        
        elif message_type == "suggestion":
            # Handle suggestion operations
            if data.get("action") == "create":
                # Broadcast new suggestion
                await rooms.broadcast(page_id, json.dumps({
                    "type": "suggestion_created",
                    "data": data
                }))
            
            elif data.get("action") == "accept":
                # Broadcast suggestion acceptance
                await rooms.broadcast(page_id, json.dumps({
                    "type": "suggestion_accepted",
                    "data": data
                }))
        
        elif message_type == "lock_request":
            # Handle soft lock requests
            result = await presence_service.acquire_soft_lock(
                page_id, user_id, data.get("resource", ""), data.get("lock_type", "edit")
            )
            
            if result["success"]:
                # Broadcast lock acquisition
                await rooms.broadcast(page_id, json.dumps({
                    "type": "lock_acquired",
                    "data": {
                        "resource": data.get("resource"),
                        "user_id": user_id,
                        "expires_at": result["expires_at"]
                    }
                }))
            else:
                # Send lock failure back to sender
                await websocket.send_text(json.dumps({
                    "type": "lock_failed",
                    "data": result
                }))
        
        elif message_type == "lock_release":
            # Handle lock release
            result = await presence_service.release_soft_lock(
                page_id, user_id, data.get("resource", "")
            )
            
            if result["success"]:
                # Broadcast lock release
                await rooms.broadcast(page_id, json.dumps({
                    "type": "lock_released",
                    "data": {
                        "resource": data.get("resource"),
                        "user_id": user_id
                    }
                }))
        
        else:
            # Echo unknown message types
            await rooms.broadcast(page_id, json.dumps(message))
            
    except Exception as e:
        logger.error(f"Error handling message type {message_type}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Failed to handle {message_type}",
            "error": str(e)
        }))


@router.get("/rooms/{page_id}/state")
async def get_room_state(page_id: int):
    """Get current state of a collaboration room"""
    try:
        page_state = await crdt_manager.get_page_state(page_id)
        presence_info = await presence_service.get_page_presence(page_id)
        
        return {
            "page_id": page_id,
            "state": page_state,
            "presence": presence_info,
            "participants": len(presence_info.get("active_users", []))
        }
    except Exception as e:
        logger.error(f"Error getting room state for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room state")


@router.get("/rooms/{page_id}/participants")
async def get_room_participants(page_id: int):
    """Get list of participants in a collaboration room"""
    try:
        presence_info = await presence_service.get_page_presence(page_id)
        participants = presence_info.get("active_users", [])
        
        return {
            "page_id": page_id,
            "participants": participants,
            "count": len(participants)
        }
    except Exception as e:
        logger.error(f"Error getting participants for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get participants")


@router.post("/rooms/{page_id}/snapshot")
async def create_room_snapshot(page_id: int):
    """Create a snapshot of the current room state"""
    try:
        snapshot_id = await crdt_manager.create_snapshot(page_id, "system")
        return {
            "page_id": page_id,
            "snapshot_id": snapshot_id,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating snapshot for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create snapshot")


@router.get("/rooms/{page_id}/snapshots")
async def get_room_snapshots(page_id: int):
    """Get list of snapshots for a room"""
    try:
        snapshots = await crdt_manager.snapshot_store.list_snapshots(page_id)
        return {
            "page_id": page_id,
            "snapshots": snapshots
        }
    except Exception as e:
        logger.error(f"Error getting snapshots for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get snapshots")


@router.post("/rooms/{page_id}/restore")
async def restore_from_snapshot(page_id: int, snapshot_id: str):
    """Restore room state from a snapshot"""
    try:
        success = await crdt_manager.restore_from_snapshot(page_id, snapshot_id)
        
        if success:
            # Broadcast restoration to all connected users
            await rooms.broadcast(page_id, json.dumps({
                "type": "state_restored",
                "data": {
                    "snapshot_id": snapshot_id,
                    "restored_at": datetime.utcnow().isoformat()
                }
            }))
            
            return {
                "page_id": page_id,
                "snapshot_id": snapshot_id,
                "success": True,
                "restored_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Snapshot not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring snapshot for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore snapshot")


@router.get("/rooms/{page_id}/operations")
async def get_operation_history(page_id: int, limit: int = 50, offset: int = 0):
    """Get operation history for a room"""
    try:
        operations = await crdt_manager.get_operation_history(page_id, limit, offset)
        return {
            "page_id": page_id,
            "operations": operations,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting operation history for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get operation history")


@router.get("/presence/stats")
async def get_global_presence_stats():
    """Get global presence statistics"""
    try:
        stats = await presence_service.get_global_presence_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting global presence stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get presence stats")
