# Comments and threads system for collaboration
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from app.models.user_models import User

logger = logging.getLogger(__name__)


class CommentsService:
    """Service for managing comments and threads in collaborative editing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_comment(
        self,
        page_id: int,
        segment_id: str,
        text: str,
        user_id: str,
        parent_comment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new comment or reply"""
        try:
            comment_id = str(uuid.uuid4())
            
            comment = {
                "id": comment_id,
                "page_id": page_id,
                "segment_id": segment_id,
                "text": text,
                "author_id": user_id,
                "parent_comment_id": parent_comment_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "resolved": False,
                "replies": [],
                "reactions": {},
                "mentions": self._extract_mentions(text)
            }
            
            # In a real implementation, save to database
            logger.info(f"Created comment {comment_id} by user {user_id}")
            
            return comment
            
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            raise
    
    async def get_comments_for_page(
        self,
        page_id: int,
        segment_id: Optional[str] = None,
        include_replies: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all comments for a page or specific segment"""
        try:
            # Mock comments for now
            mock_comments = [
                {
                    "id": f"comment_{page_id}_1",
                    "page_id": page_id,
                    "segment_id": segment_id or f"segment_{page_id}_1",
                    "text": "This translation could be improved.",
                    "author_id": "user_1",
                    "author_name": "John Doe",
                    "parent_comment_id": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "resolved": False,
                    "replies": [
                        {
                            "id": f"reply_{page_id}_1",
                            "text": "I agree, let me suggest an alternative.",
                            "author_id": "user_2",
                            "author_name": "Jane Smith",
                            "created_at": datetime.utcnow().isoformat(),
                            "resolved": False
                        }
                    ],
                    "reactions": {
                        "👍": ["user_1", "user_3"],
                        "👎": []
                    },
                    "mentions": []
                },
                {
                    "id": f"comment_{page_id}_2",
                    "page_id": page_id,
                    "segment_id": segment_id or f"segment_{page_id}_2",
                    "text": "The terminology here is inconsistent with our glossary.",
                    "author_id": "user_2",
                    "author_name": "Jane Smith",
                    "parent_comment_id": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "resolved": True,
                    "replies": [],
                    "reactions": {
                        "👍": ["user_1"],
                        "👎": []
                    },
                    "mentions": ["@user_1"]
                }
            ]
            
            # Filter by segment if specified
            if segment_id:
                mock_comments = [c for c in mock_comments if c["segment_id"] == segment_id]
            
            # Filter out replies if not requested
            if not include_replies:
                for comment in mock_comments:
                    comment["replies"] = []
            
            return mock_comments
            
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
    
    async def update_comment(
        self,
        comment_id: str,
        text: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Update a comment"""
        try:
            # Mock update for now
            updated_comment = {
                "id": comment_id,
                "text": text,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": user_id,
                "success": True
            }
            
            logger.info(f"Updated comment {comment_id} by user {user_id}")
            return updated_comment
            
        except Exception as e:
            logger.error(f"Error updating comment: {e}")
            raise
    
    async def delete_comment(
        self,
        comment_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Delete a comment"""
        try:
            # Mock deletion for now
            result = {
                "comment_id": comment_id,
                "deleted_by": user_id,
                "deleted_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(f"Deleted comment {comment_id} by user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting comment: {e}")
            raise
    
    async def resolve_comment(
        self,
        comment_id: str,
        user_id: str,
        resolution_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark a comment as resolved"""
        try:
            result = {
                "comment_id": comment_id,
                "resolved": True,
                "resolved_by": user_id,
                "resolved_at": datetime.utcnow().isoformat(),
                "resolution_note": resolution_note,
                "success": True
            }
            
            logger.info(f"Resolved comment {comment_id} by user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error resolving comment: {e}")
            raise
    
    async def add_reaction(
        self,
        comment_id: str,
        reaction: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Add a reaction to a comment"""
        try:
            # Valid reactions
            valid_reactions = ["👍", "👎", "❤️", "😂", "😮", "😢", "😡"]
            
            if reaction not in valid_reactions:
                raise ValueError(f"Invalid reaction: {reaction}")
            
            result = {
                "comment_id": comment_id,
                "reaction": reaction,
                "user_id": user_id,
                "added_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(f"Added reaction {reaction} to comment {comment_id} by user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            raise
    
    async def remove_reaction(
        self,
        comment_id: str,
        reaction: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Remove a reaction from a comment"""
        try:
            result = {
                "comment_id": comment_id,
                "reaction": reaction,
                "user_id": user_id,
                "removed_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(f"Removed reaction {reaction} from comment {comment_id} by user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error removing reaction: {e}")
            raise
    
    async def get_comment_thread(
        self,
        comment_id: str
    ) -> Dict[str, Any]:
        """Get a comment and all its replies as a thread"""
        try:
            # Mock thread for now
            thread = {
                "parent_comment": {
                    "id": comment_id,
                    "text": "This is the main comment",
                    "author_id": "user_1",
                    "author_name": "John Doe",
                    "created_at": datetime.utcnow().isoformat(),
                    "resolved": False
                },
                "replies": [
                    {
                        "id": f"reply_{comment_id}_1",
                        "text": "This is a reply to the comment",
                        "author_id": "user_2",
                        "author_name": "Jane Smith",
                        "created_at": datetime.utcnow().isoformat(),
                        "resolved": False
                    },
                    {
                        "id": f"reply_{comment_id}_2",
                        "text": "Another reply",
                        "author_id": "user_3",
                        "author_name": "Bob Wilson",
                        "created_at": datetime.utcnow().isoformat(),
                        "resolved": False
                    }
                ],
                "total_replies": 2,
                "resolved": False
            }
            
            return thread
            
        except Exception as e:
            logger.error(f"Error getting comment thread: {e}")
            return {}
    
    async def get_comments_statistics(
        self,
        page_id: int
    ) -> Dict[str, Any]:
        """Get statistics about comments for a page"""
        try:
            comments = await self.get_comments_for_page(page_id)
            
            total_comments = len(comments)
            resolved_comments = sum(1 for c in comments if c.get("resolved", False))
            unresolved_comments = total_comments - resolved_comments
            
            # Count replies
            total_replies = sum(len(c.get("replies", [])) for c in comments)
            
            # Count reactions
            total_reactions = sum(
                sum(len(users) for users in c.get("reactions", {}).values())
                for c in comments
            )
            
            # Most active users
            user_activity = {}
            for comment in comments:
                author_id = comment.get("author_id")
                if author_id:
                    user_activity[author_id] = user_activity.get(author_id, 0) + 1
                    # Count replies too
                    for reply in comment.get("replies", []):
                        reply_author = reply.get("author_id")
                        if reply_author:
                            user_activity[reply_author] = user_activity.get(reply_author, 0) + 1
            
            most_active_user = max(user_activity.items(), key=lambda x: x[1])[0] if user_activity else None
            
            return {
                "page_id": page_id,
                "total_comments": total_comments,
                "resolved_comments": resolved_comments,
                "unresolved_comments": unresolved_comments,
                "total_replies": total_replies,
                "total_reactions": total_reactions,
                "resolution_rate": resolved_comments / total_comments if total_comments > 0 else 0,
                "most_active_user": most_active_user,
                "user_activity": user_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting comments statistics: {e}")
            return {}
    
    async def search_comments(
        self,
        page_id: int,
        query: str,
        author_id: Optional[str] = None,
        resolved_only: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Search comments by text content"""
        try:
            comments = await self.get_comments_for_page(page_id)
            
            # Filter by query
            if query:
                comments = [
                    c for c in comments
                    if query.lower() in c.get("text", "").lower()
                ]
            
            # Filter by author
            if author_id:
                comments = [
                    c for c in comments
                    if c.get("author_id") == author_id
                ]
            
            # Filter by resolution status
            if resolved_only is not None:
                comments = [
                    c for c in comments
                    if c.get("resolved", False) == resolved_only
                ]
            
            return comments
            
        except Exception as e:
            logger.error(f"Error searching comments: {e}")
            return []
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text"""
        import re
        mentions = re.findall(r'@(\w+)', text)
        return mentions
    
    async def notify_mentions(
        self,
        comment_id: str,
        mentions: List[str],
        commenter_id: str
    ) -> Dict[str, Any]:
        """Notify users who were mentioned in a comment"""
        try:
            # Mock notification for now
            notifications = []
            
            for mention in mentions:
                notification = {
                    "user_id": mention,
                    "comment_id": comment_id,
                    "commenter_id": commenter_id,
                    "type": "mention",
                    "created_at": datetime.utcnow().isoformat(),
                    "read": False
                }
                notifications.append(notification)
            
            result = {
                "comment_id": comment_id,
                "notifications_sent": len(notifications),
                "notifications": notifications
            }
            
            logger.info(f"Sent {len(notifications)} mention notifications for comment {comment_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error notifying mentions: {e}")
            return {
                "comment_id": comment_id,
                "notifications_sent": 0,
                "error": str(e)
            }
