"""
SkillConverter — Base interface for all source type converters.

Every scraper/converter inherits this and implements extract().
The create command calls converter.run() — same interface for the public types.

Usage:
    converter = get_converter("web", config)
    converter.run()  # extract + build + return exit code
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SkillConverter:
    """Base interface for all skill converters.

    Subclasses must implement extract() at minimum.
    build_skill() has a default implementation that most converters override.
    """

    # Override in subclass
    SOURCE_TYPE: str = "unknown"

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unnamed")
        self.skill_dir = f"output/{self.name}"

    def run(self) -> int:
        """Main entry point — extract source and build skill.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        try:
            logger.info(f"Extracting from {self.SOURCE_TYPE} source: {self.name}")
            self.extract()
            result = self.build_skill()
            if result is False:
                logger.error(f"❌ {self.SOURCE_TYPE} build_skill() reported failure")
                return 1
            logger.info(f"✅ Skill built: {self.skill_dir}/")
            return 0
        except Exception as e:
            logger.exception(f"❌ {self.SOURCE_TYPE} extraction failed: {e}")
            return 1

    def extract(self):
        """Extract content from source. Override in subclass."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement extract()")

    def build_skill(self):
        """Build SKILL.md from extracted data. Override in subclass."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement build_skill()")


# Registry mapping source type → (module_path, class_name)
CONVERTER_REGISTRY: dict[str, tuple[str, str]] = {
    "web": ("yonyou_doc2skill.cli.doc_scraper", "DocToSkillConverter"),
    "github": ("yonyou_doc2skill.cli.github_scraper", "GitHubScraper"),
    "pdf": ("yonyou_doc2skill.cli.pdf_scraper", "PDFToSkillConverter"),
    "word": ("yonyou_doc2skill.cli.word_scraper", "WordToSkillConverter"),
    "video": ("yonyou_doc2skill.cli.video_scraper", "VideoToSkillConverter"),
    "local": ("yonyou_doc2skill.cli.codebase_scraper", "CodebaseAnalyzer"),
    "html": ("yonyou_doc2skill.cli.html_scraper", "HtmlToSkillConverter"),
    "asciidoc": ("yonyou_doc2skill.cli.asciidoc_scraper", "AsciiDocToSkillConverter"),
    "pptx": ("yonyou_doc2skill.cli.pptx_scraper", "PptxToSkillConverter"),
    "confluence": ("yonyou_doc2skill.cli.confluence_scraper", "ConfluenceToSkillConverter"),
    "chat": ("yonyou_doc2skill.cli.chat_scraper", "ChatToSkillConverter"),
    # NOTE: UnifiedScraper takes (config_path: str), not (config: dict).
    # Callers must construct it directly, not via get_converter().
    "config": ("yonyou_doc2skill.cli.unified_scraper", "UnifiedScraper"),
}


def get_converter(source_type: str, config: dict[str, Any]) -> SkillConverter:
    """Get the appropriate converter for a source type.

    Args:
        source_type: Source type from SourceDetector (web, github, pdf, etc.)
        config: Configuration dict for the converter.

    Returns:
        Initialized converter instance.

    Raises:
        ValueError: If source type is not supported.
    """
    import importlib

    if source_type not in CONVERTER_REGISTRY:
        raise ValueError(
            f"Unknown source type: {source_type}. "
            f"Supported: {', '.join(sorted(CONVERTER_REGISTRY))}"
        )

    module_path, class_name = CONVERTER_REGISTRY[source_type]
    module = importlib.import_module(module_path)
    converter_class = getattr(module, class_name, None)
    if converter_class is None:
        raise ValueError(
            f"Class '{class_name}' not found in module '{module_path}'. "
            f"Check CONVERTER_REGISTRY entry for '{source_type}'."
        )
    return converter_class(config)
