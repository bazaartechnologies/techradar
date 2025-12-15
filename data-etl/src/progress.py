"""
Progress tracking and checkpoint management.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks scanning progress with checkpoint support."""

    def __init__(self, checkpoint_path: Path, enabled: bool = True, resume: bool = False):
        """
        Initialize progress tracker.

        Args:
            checkpoint_path: Path to checkpoint file
            enabled: Enable checkpoint saving
            resume: Load existing checkpoint (resume mode)
        """
        self.checkpoint_path = checkpoint_path
        self.enabled = enabled
        self.data = {
            'scanned_repos': [],
            'start_time': None,
            'last_update': None,
            'organizations': {},
            'stats': {}
        }

        # Only load checkpoint if explicitly resuming
        if enabled and resume:
            self._load()

    def _load(self) -> None:
        """Load progress from checkpoint file."""
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, 'r') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded checkpoint: {len(self.data['scanned_repos'])} repos scanned")
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}")
                self.data['scanned_repos'] = []

    def _save(self) -> None:
        """Save progress to checkpoint file."""
        if not self.enabled:
            return

        try:
            self.data['last_update'] = datetime.now().isoformat()

            with open(self.checkpoint_path, 'w') as f:
                json.dump(self.data, f, indent=2)

            logger.debug(f"Checkpoint saved: {len(self.data['scanned_repos'])} repos")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def start_scan(self) -> None:
        """Mark scan as started."""
        if not self.data['start_time']:
            self.data['start_time'] = datetime.now().isoformat()
        self._save()

    def is_scanned(self, repo_full_name: str) -> bool:
        """
        Check if repository has been scanned.

        Args:
            repo_full_name: Full repository name (org/repo)

        Returns:
            True if already scanned
        """
        return repo_full_name in self.data['scanned_repos']

    def mark_scanned(self, repo_full_name: str, save_interval: int = 10) -> None:
        """
        Mark repository as scanned.

        Args:
            repo_full_name: Full repository name (org/repo)
            save_interval: Save checkpoint every N repos
        """
        if repo_full_name not in self.data['scanned_repos']:
            self.data['scanned_repos'].append(repo_full_name)

        # Save periodically
        if len(self.data['scanned_repos']) % save_interval == 0:
            self._save()

    def update_stats(self, stats: Dict) -> None:
        """
        Update scanning statistics.

        Args:
            stats: Statistics dictionary
        """
        self.data['stats'] = stats
        self._save()

    def get_progress(self) -> Dict:
        """Get current progress information."""
        return {
            'scanned_repos': len(self.data['scanned_repos']),
            'start_time': self.data['start_time'],
            'last_update': self.data['last_update']
        }

    def clear(self) -> None:
        """Clear checkpoint data."""
        self.data = {
            'scanned_repos': [],
            'start_time': None,
            'last_update': None,
            'organizations': {},
            'stats': {}
        }

        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()

        logger.info("Checkpoint cleared")

    def finalize(self) -> None:
        """Finalize progress tracking."""
        self.data['end_time'] = datetime.now().isoformat()
        self._save()
        logger.info("Progress tracking finalized")


class ProgressDisplay:
    """Display progress information to user."""

    def __init__(self, total: int):
        """
        Initialize progress display.

        Args:
            total: Total number of items
        """
        self.total = total
        self.current = 0
        self.start_time = datetime.now()

    def update(self, current: int, message: str = "") -> None:
        """
        Update progress display.

        Args:
            current: Current item number
            message: Optional message to display
        """
        self.current = current
        percentage = (current / self.total) * 100 if self.total > 0 else 0

        # Calculate ETA
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if current > 0:
            avg_time = elapsed / current
            remaining = (self.total - current) * avg_time
            eta_str = self._format_time(remaining)
        else:
            eta_str = "calculating..."

        # Create progress bar
        bar_width = 50
        filled = int(bar_width * current / self.total) if self.total > 0 else 0
        bar = '=' * filled + '>' + ' ' * (bar_width - filled - 1)

        # Display
        print(f"\r[{bar}] {current}/{self.total} ({percentage:.1f}%) | ETA: {eta_str} | {message}", end='', flush=True)

        if current >= self.total:
            print()  # New line when complete

    def _format_time(self, seconds: float) -> str:
        """Format seconds into readable time string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m {int(seconds % 60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def complete(self, message: str = "Complete!") -> None:
        """Mark progress as complete."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        elapsed_str = self._format_time(elapsed)
        print(f"\n✓ {message} (took {elapsed_str})")
