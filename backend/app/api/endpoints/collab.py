# Collaboration WebSocket endpoints
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List
import json
import logging
from datetime import datetime

from app.services.collab.room_manager import RoomManager
from app.api.endpoints.auth import get_current_user_ws
from app.models.user_models import User

logger = logging.getLogger(__name__)

router = APIRouter()
room_manager = RoomManager()


@router.websocket("/{page_id}")
async def collab_websocket(websocket: WebSocket, page_id: int):
    """WebSocket endpoint for real-time collaboration on a page"""
    await websocket.accept()
    
    try:
        # Add client to room
        await room_manager.connect(page_id, websocket)
        logger.info(f"Client connected to page {page_id}")
        
        # Send initial room state
        room_state = await room_manager.get_room_state(page_id)
        await websocket.send_text(json.dumps({
            "type": "room_state",
            "data": room_state
        }))
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_message(page_id, websocket, message)
                
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
        await room_manager.disconnect(page_id, websocket)
        logger.info(f"Client disconnected from page {page_id}")
    except Exception as e:
        logger.error(f"WebSocket error for page {page_id}: {e}")
        await room_manager.disconnect(page_id, websocket)


async def handle_message(page_id: int, websocket: WebSocket, message: Dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    elif message_type == "presence":
        # Update user presence
        await room_manager.update_presence(
            page_id, 
            websocket, 
            message.get("data", {})
        )
    
    elif message_type == "operation":
        # Handle CRDT operation
        await room_manager.broadcast_operation(
            page_id,
            websocket,
            message.get("data", {})
        )
    
    elif message_type == "comment":
        # Handle comment operations
        await room_manager.broadcast_comment(
            page_id,
            websocket,
            message.get("data", {})
        )
    
    elif message_type == "suggestion":
        # Handle suggestion operations
        await room_manager.broadcast_suggestion(
            page_id,
            websocket,
            message.get("data", {})
        )
    
    else:
        # Echo unknown message types
        await room_manager.broadcast_to_room(
            page_id,
            websocket,
            message
        )


@router.get("/rooms/{page_id}/state")
async def get_room_state(page_id: int):
    """Get current state of a collaboration room"""
    try:
        state = await room_manager.get_room_state(page_id)
        return {
            "page_id": page_id,
            "state": state,
            "participants": len(room_manager.get_room_participants(page_id))
        }
    except Exception as e:
        logger.error(f"Error getting room state for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room state")


@router.get("/rooms/{page_id}/participants")
async def get_room_participants(page_id: int):
    """Get list of participants in a collaboration room"""
    try:
        participants = room_manager.get_room_participants(page_id)
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
        snapshot_id = await room_manager.create_snapshot(page_id)
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
        snapshots = await room_manager.get_snapshots(page_id)
        return {
            "page_id": page_id,
            "snapshots": snapshots
        }
    except Exception as e:
        logger.error(f"Error getting snapshots for page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get snapshots")
