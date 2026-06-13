"""Draft publisher — save the approved post to a file (+ clipboard).

The zero-setup publishing path: works with no external accounts. Clipboard copy
is best-effort and degrades gracefully on headless systems.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from post_it.models import ApprovedPost, PublishResult
from post_it.publishers.base import SocialPublisher


class DraftPublisher(SocialPublisher):
    name: ClassVar[str] = "draft"

    def __init__(self, *, draft_dir: Path) -> None:
        self.draft_dir = Path(draft_dir)

    def publish(self, approved: ApprovedPost) -> PublishResult:
        text = approved.variant.text
        self.validate(text, platform=approved.platform)

        self.draft_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = self.draft_dir / f"post-{stamp}.txt"
        path.write_text(text + "\n", encoding="utf-8")

        detail = "Saved draft."
        if self._copy_to_clipboard(text):
            detail = "Saved draft and copied to clipboard."

        return PublishResult(
            mode="draft", success=True, location=str(path), detail=detail
        )

    @staticmethod
    def _copy_to_clipboard(text: str) -> bool:
        try:
            import pyperclip

            pyperclip.copy(text)
            return True
        except Exception:
            # No clipboard backend (headless/CI) — file write still succeeded.
            return False
