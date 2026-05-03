"""
Rembg Image Background Remover.
"""
import logging
from PIL import Image
from rembg import remove, new_session

logger = logging.getLogger("runpod-rembg")

VALID_MODELS = [
    "u2net",
    "u2netp",
    "u2net_human_seg",
    "u2net_cloth_seg",
    "silueta",
    "isnet-general-use",
    "isnet-anime",
    "birefnet-general",
    "birefnet-general-lite",
    "birefnet-portrait",
    "birefnet-dis",
    "birefnet-hrsod",
    "birefnet-cod",
    "birefnet-massive",
    "bria-rmbg",
]


class ImageRemover:
    """
    Rembg image background remover.
    Caches sessions per model for performance.
    """

    def __init__(self):
        """Initialize remover with empty session cache."""
        self._sessions = {}

    def _get_session(self, model: str):
        """Load and cache rembg session for a given model."""
        if model not in self._sessions:
            self._sessions[model] = new_session(model)
            logger.info("Loaded rembg session for model: %s", model)
        return self._sessions[model]

    def remove_background(self, image: Image.Image, model: str = "u2net") -> Image.Image:
        """
        Remove background from image.

        Args:
            image: Input PIL Image (RGB)
            model: Rembg model name (default: u2net)

        Returns:
            PIL Image with background removed (RGBA)

        Raises:
            ValueError: If model is not supported
        """
        if model not in VALID_MODELS:
            raise ValueError(
                f"Unsupported model: {model}. Must be one of {VALID_MODELS}"
            )

        session = self._get_session(model)
        output = remove(image, session=session)
        return output
