"""Telegraph service for publishing long-form content."""

from telegraph import Telegraph
from telegraph.exceptions import TelegraphException


class TelegraphService:
    """Service for publishing content to Telegraph."""

    def __init__(self):
        """Initialize Telegraph service."""
        self.telegraph = Telegraph()
        self._token = None

    async def ensure_account(self) -> None:
        """Ensure Telegraph account is created."""
        if self._token:
            return

        try:
            response = self.telegraph.create_account(
                short_name="AdtroBot",
                author_name="AdtroBot",
                author_url="https://t.me/adtro_bot"
            )
            self._token = response["access_token"]
        except TelegraphException:
            # Account might already exist, try to get token
            pass

    async def publish_article(
        self,
        title: str,
        content: str,
        author: str = "AdtroBot"
    ) -> str:
        """Publish article to Telegraph.

        Args:
            title: Article title
            content: Article content (plain text or HTML)
            author: Author name

        Returns:
            Telegraph article URL
        """
        await self.ensure_account()

        # Convert plain text to Telegraph HTML format
        html_content = self._format_content(content)

        try:
            response = self.telegraph.create_page(
                title=title,
                html_content=html_content,
                author_name=author
            )
            return response["url"]
        except TelegraphException as e:
            raise RuntimeError(f"Failed to publish to Telegraph: {e}")

    def _format_content(self, content: str) -> str:
        """Format content for Telegraph.

        Args:
            content: Plain text content

        Returns:
            HTML formatted content
        """
        # Split by sections (marked with [SECTION])
        sections = []
        current_section = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                if current_section:
                    sections.append("\n".join(current_section))
                    current_section = []
                continue

            # Section headers in square brackets
            if line.startswith("[") and line.endswith("]"):
                if current_section:
                    sections.append("\n".join(current_section))
                    current_section = []
                # Add section header as <h3>
                section_title = line[1:-1]
                current_section.append(f"<h3>{section_title}</h3>")
            else:
                current_section.append(f"<p>{line}</p>")

        if current_section:
            sections.append("\n".join(current_section))

        return "\n".join(sections)


# Singleton instance
_telegraph_service: TelegraphService | None = None


def get_telegraph_service() -> TelegraphService:
    """Get Telegraph service instance.

    Returns:
        TelegraphService instance
    """
    global _telegraph_service
    if _telegraph_service is None:
        _telegraph_service = TelegraphService()
    return _telegraph_service
