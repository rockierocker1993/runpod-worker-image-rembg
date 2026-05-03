"""
Rembg Image Background Remover.
"""
import os
import logging
from PIL import Image

logger = logging.getLogger("runpod-rembg")

# Set U2NET_HOME BEFORE importing rembg — rembg reads this at import time
_U2NET_HOME = os.environ.get("U2NET_HOME", "/runpod-volume/u2net-models")
os.environ["U2NET_HOME"] = _U2NET_HOME

from rembg import remove, new_session  # noqa: E402

VALID_MODELS = [
    "u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg",
    "silueta", "isnet-general-use", "isnet-anime",
    "birefnet-general", "birefnet-general-lite", "birefnet-portrait",
    "birefnet-dis", "birefnet-hrsod", "birefnet-cod", "birefnet-massive",
    "bria-rmbg"
]

_PROVIDERS = ["CUDAExecutionProvider"]


class ImageRemover:
    def __init__(self):
        self._sessions = {}
        logger.info("ImageRemover initialized | U2NET_HOME=%s", _U2NET_HOME)
        self._verify_gpu()

    def _verify_gpu(self) -> None:
        import onnxruntime as ort
        available = ort.get_available_providers()
        if "CUDAExecutionProvider" not in available:
            raise RuntimeError(
                f"CUDAExecutionProvider not available. Available: {available}"
            )
        logger.info("GPU verified | CUDAExecutionProvider available | all_providers=%s", available)

    def _get_session(self, model: str):
        if model not in self._sessions:
            self._sessions[model] = new_session(model, providers=_PROVIDERS)
            logger.info("Loaded rembg session | model=%s | U2NET_HOME=%s", model, _U2NET_HOME)
        return self._sessions[model]

    def remove_background(self, image: Image.Image, model: str = "u2net") -> Image.Image:
        if model not in VALID_MODELS:
            raise ValueError(f"Unsupported model: {model}. Must be one of {VALID_MODELS}")
        session = self._get_session(model)
        output = remove(image, session=session)
        return output