# CRDT snapshot store for collaboration state persistence
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pickle
import base64

logger = logging.getLogger(__name__)


class SnapshotStore:
    """Store and manage CRDT snapshots for collaboration"""
    
    def __init__(self, storage_backend: str = "memory"):
        self.storage_backend = storage_backend
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.cleanup_task = None
        # Don't start cleanup task during initialization to avoid event loop issues
        # self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task for old snapshots"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_old_snapshots())
    
    async def _cleanup_old_snapshots(self):
        """Background task to clean up old snapshots"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.utcnow() - timedelta(days=7)  # Keep snapshots for 7 days
                
                snapshots_to_remove = []
                for snapshot_id, snapshot_data in self.snapshots.items():
                    created_at = datetime.fromisoformat(snapshot_data.get("created_at", ""))
                    if created_at < cutoff_time:
                        snapshots_to_remove.append(snapshot_id)
                
                for snapshot_id in snapshots_to_remove:
                    del self.snapshots[snapshot_id]
                
                if snapshots_to_remove:
                    logger.info(f"Cleaned up {len(snapshots_to_remove)} old snapshots")
                
            except Exception as e:
                logger.error(f"Error in snapshot cleanup task: {e}")
    
    async def create_snapshot(
        self, 
        page_id: int, 
        state: Dict[str, Any],
        created_by: str,
        version: int = 1
    ) -> str:
        """Create a new snapshot of the collaboration state"""
        try:
            snapshot_id = str(uuid.uuid4())
            
            # Compress and encode the state
            compressed_state = self._compress_state(state)
            
            snapshot_data = {
                "id": snapshot_id,
                "page_id": page_id,
                "version": version,
                "state": compressed_state,
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat(),
                "size_bytes": len(compressed_state)
            }
            
            self.snapshots[snapshot_id] = snapshot_data
            
            logger.info(f"Created snapshot {snapshot_id} for page {page_id}")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            raise
    
    async def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get a snapshot by ID"""
        try:
            if snapshot_id not in self.snapshots:
                return None
            
            snapshot_data = self.snapshots[snapshot_id].copy()
            
            # Decompress the state
            snapshot_data["state"] = self._decompress_state(snapshot_data["state"])
            
            return snapshot_data
            
        except Exception as e:
            logger.error(f"Error getting snapshot: {e}")
            return None
    
    async def get_latest_snapshot(self, page_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot for a page"""
        try:
            page_snapshots = [
                snapshot for snapshot in self.snapshots.values()
                if snapshot["page_id"] == page_id
            ]
            
            if not page_snapshots:
                return None
            
            # Sort by creation time and version
            latest_snapshot = max(
                page_snapshots, 
                key=lambda s: (s["created_at"], s["version"])
            )
            
            # Decompress the state
            latest_snapshot = latest_snapshot.copy()
            latest_snapshot["state"] = self._decompress_state(latest_snapshot["state"])
            
            return latest_snapshot
            
        except Exception as e:
            logger.error(f"Error getting latest snapshot: {e}")
            return None
    
    async def list_snapshots(
        self, 
        page_id: int, 
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List snapshots for a page"""
        try:
            page_snapshots = [
                snapshot for snapshot in self.snapshots.values()
                if snapshot["page_id"] == page_id
            ]
            
            # Sort by creation time (newest first)
            page_snapshots.sort(key=lambda s: s["created_at"], reverse=True)
            
            # Apply pagination
            paginated_snapshots = page_snapshots[offset:offset + limit]
            
            # Remove state data to reduce payload size
            for snapshot in paginated_snapshots:
                snapshot.pop("state", None)
            
            return paginated_snapshots
            
        except Exception as e:
            logger.error(f"Error listing snapshots: {e}")
            return []
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot"""
        try:
            if snapshot_id in self.snapshots:
                del self.snapshots[snapshot_id]
                logger.info(f"Deleted snapshot {snapshot_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting snapshot: {e}")
            return False
    
    async def compact_snapshots(self, page_id: int, keep_count: int = 5) -> int:
        """Compact snapshots for a page, keeping only the most recent ones"""
        try:
            page_snapshots = [
                (snapshot_id, snapshot) for snapshot_id, snapshot in self.snapshots.items()
                if snapshot["page_id"] == page_id
            ]
            
            if len(page_snapshots) <= keep_count:
                return 0
            
            # Sort by creation time (newest first)
            page_snapshots.sort(key=lambda s: s[1]["created_at"], reverse=True)
            
            # Keep the most recent snapshots
            snapshots_to_keep = page_snapshots[:keep_count]
            snapshots_to_delete = page_snapshots[keep_count:]
            
            # Delete old snapshots
            deleted_count = 0
            for snapshot_id, _ in snapshots_to_delete:
                if await self.delete_snapshot(snapshot_id):
                    deleted_count += 1
            
            logger.info(f"Compacted {deleted_count} snapshots for page {page_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error compacting snapshots: {e}")
            return 0
    
    def _compress_state(self, state: Dict[str, Any]) -> str:
        """Compress state data for storage"""
        try:
            # Serialize to JSON first
            json_data = json.dumps(state, default=str)
            
            # Compress using pickle (in production, use more efficient compression)
            compressed_data = pickle.dumps(json_data)
            
            # Encode to base64 for storage
            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
            
            return encoded_data
            
        except Exception as e:
            logger.error(f"Error compressing state: {e}")
            return json.dumps(state, default=str)
    
    def _decompress_state(self, compressed_state: str) -> Dict[str, Any]:
        """Decompress state data from storage"""
        try:
            # Decode from base64
            compressed_data = base64.b64decode(compressed_state.encode('utf-8'))
            
            # Decompress using pickle
            json_data = pickle.loads(compressed_data)
            
            # Parse JSON
            state = json.loads(json_data)
            
            return state
            
        except Exception as e:
            logger.error(f"Error decompressing state: {e}")
            # Fallback to treating as JSON
            try:
                return json.loads(compressed_state)
            except:
                return {}
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_snapshots = len(self.snapshots)
            total_size = sum(snapshot.get("size_bytes", 0) for snapshot in self.snapshots.values())
            
            # Group by page
            pages = {}
            for snapshot in self.snapshots.values():
                page_id = snapshot["page_id"]
                if page_id not in pages:
                    pages[page_id] = 0
                pages[page_id] += 1
            
            return {
                "total_snapshots": total_snapshots,
                "total_size_bytes": total_size,
                "pages_with_snapshots": len(pages),
                "average_snapshots_per_page": total_snapshots / len(pages) if pages else 0,
                "storage_backend": self.storage_backend
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
    
    async def export_snapshots(self, page_id: int) -> Dict[str, Any]:
        """Export all snapshots for a page"""
        try:
            page_snapshots = await self.list_snapshots(page_id, limit=1000)  # Get all
            
            # Get full snapshot data
            full_snapshots = []
            for snapshot in page_snapshots:
                full_snapshot = await self.get_snapshot(snapshot["id"])
                if full_snapshot:
                    full_snapshots.append(full_snapshot)
            
            return {
                "page_id": page_id,
                "exported_at": datetime.utcnow().isoformat(),
                "snapshot_count": len(full_snapshots),
                "snapshots": full_snapshots
            }
            
        except Exception as e:
            logger.error(f"Error exporting snapshots: {e}")
            return {
                "page_id": page_id,
                "exported_at": datetime.utcnow().isoformat(),
                "snapshot_count": 0,
                "snapshots": [],
                "error": str(e)
            }
    
    async def import_snapshots(self, page_id: int, snapshots_data: List[Dict[str, Any]]) -> int:
        """Import snapshots for a page"""
        try:
            imported_count = 0
            
            for snapshot_data in snapshots_data:
                try:
                    # Create snapshot with imported data
                    snapshot_id = await self.create_snapshot(
                        page_id=page_id,
                        state=snapshot_data.get("state", {}),
                        created_by=snapshot_data.get("created_by", "import"),
                        version=snapshot_data.get("version", 1)
                    )
                    
                    if snapshot_id:
                        imported_count += 1
                        
                except Exception as e:
                    logger.error(f"Error importing snapshot: {e}")
                    continue
            
            logger.info(f"Imported {imported_count} snapshots for page {page_id}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing snapshots: {e}")
            return 0
