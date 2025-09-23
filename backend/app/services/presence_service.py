# Presence and soft locks service for real-time collaboration
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


class PresenceService:
    """Service for managing user presence and soft locks in collaborative editing"""
    
    def __init__(self):
        self.active_users: Dict[int, Dict[str, Any]] = {}  # page_id -> {user_id: user_info}
        self.user_activities: Dict[str, Dict[str, Any]] = {}  # user_id -> activity_info
        self.soft_locks: Dict[int, Dict[str, Any]] = {}  # page_id -> {resource: lock_info}
        self.cursor_positions: Dict[int, Dict[str, Any]] = {}  # page_id -> {user_id: cursor_info}
        self.selection_ranges: Dict[int, Dict[str, Any]] = {}  # page_id -> {user_id: selection_info}
    
    async def join_page(
        self,
        page_id: int,
        user_id: str,
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """User joins a page"""
        try:
            if page_id not in self.active_users:
                self.active_users[page_id] = {}
            
            # Add user to active users
            self.active_users[page_id][user_id] = {
                "user_id": user_id,
                "username": user_info.get("username", "Unknown"),
                "role": user_info.get("role", "editor"),
                "color": user_info.get("color", self._generate_user_color(user_id)),
                "joined_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            # Update user activity
            self.user_activities[user_id] = {
                "current_page": page_id,
                "last_activity": datetime.utcnow().isoformat(),
                "activity_type": "page_join"
            }
            
            # Initialize cursor and selection tracking
            if page_id not in self.cursor_positions:
                self.cursor_positions[page_id] = {}
            if page_id not in self.selection_ranges:
                self.selection_ranges[page_id] = {}
            
            result = {
                "page_id": page_id,
                "user_id": user_id,
                "action": "joined",
                "active_users": list(self.active_users[page_id].keys()),
                "user_count": len(self.active_users[page_id])
            }
            
            logger.info(f"User {user_id} joined page {page_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error joining page: {e}")
            raise
    
    async def leave_page(
        self,
        page_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """User leaves a page"""
        try:
            if page_id not in self.active_users:
                return {"success": False, "message": "Page not found"}
            
            # Remove user from active users
            if user_id in self.active_users[page_id]:
                del self.active_users[page_id][user_id]
            
            # Release any soft locks held by this user
            await self._release_user_locks(page_id, user_id)
            
            # Clear cursor and selection data
            self.cursor_positions[page_id].pop(user_id, None)
            self.selection_ranges[page_id].pop(user_id, None)
            
            # Update user activity
            if user_id in self.user_activities:
                self.user_activities[user_id]["last_activity"] = datetime.utcnow().isoformat()
                self.user_activities[user_id]["activity_type"] = "page_leave"
                self.user_activities[user_id]["current_page"] = None
            
            # Clean up empty page data
            if not self.active_users[page_id]:
                del self.active_users[page_id]
                del self.cursor_positions[page_id]
                del self.selection_ranges[page_id]
                del self.soft_locks[page_id]
            
            result = {
                "page_id": page_id,
                "user_id": user_id,
                "action": "left",
                "active_users": list(self.active_users.get(page_id, {}).keys()),
                "user_count": len(self.active_users.get(page_id, {}))
            }
            
            logger.info(f"User {user_id} left page {page_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error leaving page: {e}")
            raise
    
    async def update_cursor_position(
        self,
        page_id: int,
        user_id: str,
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's cursor position"""
        try:
            if page_id not in self.cursor_positions:
                self.cursor_positions[page_id] = {}
            
            self.cursor_positions[page_id][user_id] = {
                "position": position,
                "updated_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            # Update last seen
            if page_id in self.active_users and user_id in self.active_users[page_id]:
                self.active_users[page_id][user_id]["last_seen"] = datetime.utcnow().isoformat()
            
            return {
                "page_id": page_id,
                "user_id": user_id,
                "cursor_position": position,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error updating cursor position: {e}")
            raise
    
    async def update_selection_range(
        self,
        page_id: int,
        user_id: str,
        selection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's text selection range"""
        try:
            if page_id not in self.selection_ranges:
                self.selection_ranges[page_id] = {}
            
            self.selection_ranges[page_id][user_id] = {
                "selection": selection,
                "updated_at": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            return {
                "page_id": page_id,
                "user_id": user_id,
                "selection_range": selection,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error updating selection range: {e}")
            raise
    
    async def acquire_soft_lock(
        self,
        page_id: int,
        user_id: str,
        resource: str,
        lock_type: str = "edit"
    ) -> Dict[str, Any]:
        """Acquire a soft lock on a resource"""
        try:
            if page_id not in self.soft_locks:
                self.soft_locks[page_id] = {}
            
            lock_id = str(uuid.uuid4())
            lock_info = {
                "id": lock_id,
                "user_id": user_id,
                "resource": resource,
                "lock_type": lock_type,
                "acquired_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "auto_renew": True
            }
            
            # Check if resource is already locked
            existing_lock = self.soft_locks[page_id].get(resource)
            if existing_lock and existing_lock["user_id"] != user_id:
                # Check if existing lock has expired
                expires_at = datetime.fromisoformat(existing_lock["expires_at"])
                if datetime.utcnow() < expires_at:
                    return {
                        "success": False,
                        "message": "Resource is already locked by another user",
                        "locked_by": existing_lock["user_id"],
                        "expires_at": existing_lock["expires_at"]
                    }
            
            self.soft_locks[page_id][resource] = lock_info
            
            result = {
                "success": True,
                "lock_id": lock_id,
                "resource": resource,
                "lock_type": lock_type,
                "expires_at": lock_info["expires_at"]
            }
            
            logger.info(f"User {user_id} acquired soft lock on {resource} in page {page_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error acquiring soft lock: {e}")
            raise
    
    async def release_soft_lock(
        self,
        page_id: int,
        user_id: str,
        resource: str
    ) -> Dict[str, Any]:
        """Release a soft lock on a resource"""
        try:
            if page_id not in self.soft_locks:
                return {"success": False, "message": "No locks found for page"}
            
            if resource not in self.soft_locks[page_id]:
                return {"success": False, "message": "Resource not locked"}
            
            lock_info = self.soft_locks[page_id][resource]
            if lock_info["user_id"] != user_id:
                return {"success": False, "message": "Lock not owned by user"}
            
            del self.soft_locks[page_id][resource]
            
            result = {
                "success": True,
                "resource": resource,
                "released_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"User {user_id} released soft lock on {resource} in page {page_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error releasing soft lock: {e}")
            raise
    
    async def renew_soft_lock(
        self,
        page_id: int,
        user_id: str,
        resource: str
    ) -> Dict[str, Any]:
        """Renew a soft lock to extend its expiration"""
        try:
            if page_id not in self.soft_locks:
                return {"success": False, "message": "No locks found for page"}
            
            if resource not in self.soft_locks[page_id]:
                return {"success": False, "message": "Resource not locked"}
            
            lock_info = self.soft_locks[page_id][resource]
            if lock_info["user_id"] != user_id:
                return {"success": False, "message": "Lock not owned by user"}
            
            # Extend expiration by 5 minutes
            lock_info["expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            
            result = {
                "success": True,
                "resource": resource,
                "new_expires_at": lock_info["expires_at"]
            }
            
            logger.info(f"User {user_id} renewed soft lock on {resource} in page {page_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error renewing soft lock: {e}")
            raise
    
    async def get_page_presence(self, page_id: int) -> Dict[str, Any]:
        """Get current presence information for a page"""
        try:
            active_users = self.active_users.get(page_id, {})
            cursor_positions = self.cursor_positions.get(page_id, {})
            selection_ranges = self.selection_ranges.get(page_id, {})
            locks = self.soft_locks.get(page_id, {})
            
            # Filter out expired locks
            current_time = datetime.utcnow()
            valid_locks = {}
            for resource, lock_info in locks.items():
                expires_at = datetime.fromisoformat(lock_info["expires_at"])
                if current_time < expires_at:
                    valid_locks[resource] = lock_info
            
            return {
                "page_id": page_id,
                "active_users": list(active_users.values()),
                "user_count": len(active_users),
                "cursor_positions": cursor_positions,
                "selection_ranges": selection_ranges,
                "soft_locks": valid_locks,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting page presence: {e}")
            return {}
    
    async def get_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Get activity information for a user"""
        try:
            activity = self.user_activities.get(user_id, {})
            
            return {
                "user_id": user_id,
                "current_page": activity.get("current_page"),
                "last_activity": activity.get("last_activity"),
                "activity_type": activity.get("activity_type"),
                "is_active": self._is_user_active(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return {}
    
    async def cleanup_expired_locks(self) -> int:
        """Clean up expired soft locks"""
        try:
            current_time = datetime.utcnow()
            cleaned_count = 0
            
            for page_id, locks in self.soft_locks.items():
                expired_resources = []
                
                for resource, lock_info in locks.items():
                    expires_at = datetime.fromisoformat(lock_info["expires_at"])
                    if current_time >= expires_at:
                        expired_resources.append(resource)
                
                for resource in expired_resources:
                    del locks[resource]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired soft locks")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired locks: {e}")
            return 0
    
    async def _release_user_locks(self, page_id: int, user_id: str):
        """Release all locks held by a user on a page"""
        try:
            if page_id not in self.soft_locks:
                return
            
            locks_to_release = []
            for resource, lock_info in self.soft_locks[page_id].items():
                if lock_info["user_id"] == user_id:
                    locks_to_release.append(resource)
            
            for resource in locks_to_release:
                del self.soft_locks[page_id][resource]
            
            if locks_to_release:
                logger.info(f"Released {len(locks_to_release)} locks for user {user_id} on page {page_id}")
                
        except Exception as e:
            logger.error(f"Error releasing user locks: {e}")
    
    def _generate_user_color(self, user_id: str) -> str:
        """Generate a consistent color for a user"""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
        ]
        
        # Use user_id to consistently assign colors
        color_index = hash(user_id) % len(colors)
        return colors[color_index]
    
    def _is_user_active(self, user_id: str) -> bool:
        """Check if a user is currently active"""
        try:
            activity = self.user_activities.get(user_id, {})
            if not activity.get("last_activity"):
                return False
            
            last_activity = datetime.fromisoformat(activity["last_activity"])
            # Consider user active if last activity was within 5 minutes
            return datetime.utcnow() - last_activity < timedelta(minutes=5)
            
        except Exception as e:
            logger.error(f"Error checking user activity: {e}")
            return False
    
    async def get_global_presence_stats(self) -> Dict[str, Any]:
        """Get global presence statistics"""
        try:
            total_active_users = sum(len(users) for users in self.active_users.values())
            total_pages = len(self.active_users)
            total_locks = sum(len(locks) for locks in self.soft_locks.values())
            
            # Count users by role
            role_counts = {}
            for page_users in self.active_users.values():
                for user_info in page_users.values():
                    role = user_info.get("role", "editor")
                    role_counts[role] = role_counts.get(role, 0) + 1
            
            return {
                "total_active_users": total_active_users,
                "total_pages": total_pages,
                "total_locks": total_locks,
                "role_distribution": role_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global presence stats: {e}")
            return {}
