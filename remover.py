"""
Rembg Image Background Remover.
Supports built-in rembg models + custom ONNX model path.
"""
import os
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
    "bria-rmbg"
]

U2NET_HOME = os.environ.get("U2NET_HOME", "/runpod-volume/u2net-models/")


class ImageRemover:
    """
    Rembg image background remover.
    Caches sessions per model for performance.
    """

    def __init__(self):
        self._sessions = {}

    def _get_session(self, model: str):
        """
        Load and cache rembg session.
        """

        if model not in self._sessions:
            model_path = os.path.join(U2NET_HOME, '/') if not U2NET_HOME.endswith('/') else U2NET_HOME
            model_path = os.path.join(model_path, f"{model}.onnx")
            self._sessions[model] = new_session(
                    model,
                    model_path=model_path
                )
            logger.info("Loaded custom model: %s", model_path)

        return self._sessions[model]

    def remove_background(
        self,
        image: Image.Image,
        model: str = "u2net"
    ) -> Image.Image:
        """
        Remove background from image.
        """

        if model not in VALID_MODELS:
            raise ValueError(
                f"Unsupported model: {model}. Must be one of {VALID_MODELS}"
            )

        session = self._get_session(model)
        output = remove(image, session=session)
        return output