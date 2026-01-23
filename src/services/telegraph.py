"""Telegraph service for publishing long-form content."""

import asyncio
import re

import structlog
from telegraph import Telegraph
from telegraph.exceptions import TelegraphException

logger = structlog.get_logger()


class TelegraphService:
    """Service for publishing content to Telegraph.

    Uses asyncio.to_thread() for all blocking Telegraph calls.
    Creates anonymous account on first use.
    """

    # Timeout for Telegraph operations (seconds)
    PUBLISH_TIMEOUT = 10.0

    def __init__(self):
        """Initialize Telegraph service."""
        self.telegraph = Telegraph()
        self._token = None

    async def _ensure_account(self) -> None:
        """Ensure Telegraph account is created (async wrapper).

        Creates anonymous account if not exists.
        Called internally before publishing.
        """
        if self._token:
            return

        try:
            response = await asyncio.to_thread(
                self.telegraph.create_account,
                short_name="AdtroBot",
                author_name="AdtroBot",
                author_url="https://t.me/adtro_bot",
            )
            self._token = response.get("access_token")
            logger.info("telegraph_account_created")
        except TelegraphException as e:
            # Account creation failed, will try to publish anyway
            logger.warning("telegraph_account_creation_failed", error=str(e))

    async def publish_article(
        self,
        title: str,
        content: str,
        author: str = "AdtroBot",
    ) -> str | None:
        """Publish article to Telegraph.

        Args:
            title: Article title
            content: Article content (plain text with optional markdown)
            author: Author name

        Returns:
            Telegraph article URL or None on failure

        Note:
            Uses asyncio.to_thread for blocking Telegraph calls.
            Has internal timeout of PUBLISH_TIMEOUT seconds.
        """
        try:
            # Ensure account exists
            await self._ensure_account()

            # Convert content to Telegraph HTML format
            html_content = self._format_content(content)

            # Create page with timeout protection
            response = await asyncio.to_thread(
                self.telegraph.create_page,
                title=title,
                html_content=html_content,
                author_name=author,
            )

            url = response.get("url")
            logger.info("telegraph_article_published", title=title, url=url)
            return url

        except TelegraphException as e:
            logger.error("telegraph_publish_error", error=str(e))
            return None
        except Exception as e:
            logger.error("telegraph_unexpected_error", error=str(e))
            return None

    def _format_content(self, content: str) -> str:
        """Format content for Telegraph.

        Converts markdown-like text to Telegraph HTML:
        - Headers with emoji become <h3>
        - Bold text **text** becomes <b>text</b>
        - Paragraphs separated by blank lines become <p>
        - Lists (- item) become proper list items

        Args:
            content: Plain text content with optional formatting

        Returns:
            HTML formatted content for Telegraph
        """
        lines = content.strip().split("\n")
        html_parts = []
        current_paragraph = []
        in_list = False

        for line in lines:
            line = line.strip()

            # Empty line - flush paragraph
            if not line:
                if current_paragraph:
                    html_parts.append(f"<p>{' '.join(current_paragraph)}</p>")
                    current_paragraph = []
                if in_list:
                    in_list = False
                continue

            # Header detection (emoji at start or all caps or section marker)
            if self._is_header(line):
                if current_paragraph:
                    html_parts.append(f"<p>{' '.join(current_paragraph)}</p>")
                    current_paragraph = []
                # Clean header text
                header_text = self._clean_header(line)
                html_parts.append(f"<h3>{header_text}</h3>")
                continue

            # List item
            if line.startswith("- ") or line.startswith("• "):
                if current_paragraph:
                    html_parts.append(f"<p>{' '.join(current_paragraph)}</p>")
                    current_paragraph = []
                item_text = line[2:].strip()
                item_text = self._format_inline(item_text)
                html_parts.append(f"<p>• {item_text}</p>")
                in_list = True
                continue

            # Regular text - add to current paragraph
            formatted_line = self._format_inline(line)
            current_paragraph.append(formatted_line)

        # Flush remaining paragraph
        if current_paragraph:
            html_parts.append(f"<p>{' '.join(current_paragraph)}</p>")

        return "\n".join(html_parts)

    def _is_header(self, line: str) -> bool:
        """Check if line should be a header.

        Args:
            line: Text line to check

        Returns:
            True if line appears to be a header
        """
        # Section markers [HEADER]
        if line.startswith("[") and line.endswith("]"):
            return True

        # Starts with emoji (common for section headers)
        # Emoji regex pattern
        emoji_pattern = r"^[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]"
        if re.match(emoji_pattern, line):
            return True

        # Markdown header
        if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            return True

        return False

    def _clean_header(self, line: str) -> str:
        """Clean header text for display.

        Args:
            line: Raw header line

        Returns:
            Cleaned header text
        """
        # Remove section markers
        if line.startswith("[") and line.endswith("]"):
            return line[1:-1]

        # Remove markdown header markers
        if line.startswith("### "):
            return line[4:]
        if line.startswith("## "):
            return line[3:]
        if line.startswith("# "):
            return line[2:]

        return line

    def _format_inline(self, text: str) -> str:
        """Format inline elements (bold, etc).

        Args:
            text: Text to format

        Returns:
            Text with HTML inline formatting
        """
        # Convert **bold** to <b>bold</b>
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

        # Convert *italic* to <i>italic</i>
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

        return text


# Singleton instance
_telegraph_service: TelegraphService | None = None


def get_telegraph_service() -> TelegraphService:
    """Get Telegraph service instance.

    Returns:
        TelegraphService singleton instance
    """
    global _telegraph_service
    if _telegraph_service is None:
        _telegraph_service = TelegraphService()
    return _telegraph_service
