# БУДЕТ ПЕРЕПИСАНО ПОЛНОСТЬЮ

# import functools
# import json
# import logging
# import os
# from pathlib import Path

# import cv2
# import numpy as np

# from vk_photostylist.cv2_modules import (
#     BackgroundBlur,
#     BackgroundRemove,
#     ColorConversion,
#     GaussianBlur,
#     Inv,
# )

# logger = logging.getLogger(__name__)

# MAX_SIDE = 1280
# JPEG_QUALITY = 95
# BLUR_KERNEL_SIZE = 21

# class StyleError(Exception):
#     """Ошибка, текст которой можно показать пользователю"""

# def _to_ndarray(image: np.ndarray | cv2.UMat) -> np.ndarray:
#     return image.get() if isinstance(image, cv2.UMat) else image

# def _ensure_bgr(image: np.ndarray) -> np.ndarray:
#     if image.ndim == 2:
#         return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
#     return image

# def _limit_size(image: np.ndarray) -> np.ndarray:
#     h, w = image.shape[:2]
#     scale = MAX_SIDE / max(h, w)
#     if scale >= 1:
#         return image
#     return cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)

# _color = ColorConversion()
# _inv = Inv()
# _blur = GaussianBlur(BLUR_KERNEL_SIZE)

# def _sam_config() -> tuple[Path, Path, str]:
#     encoder = Path(
#         os.getenv("SAM_ENCODER_PATH", "models/mobilesam_int8/mobile_sam.encoder.quant.onnx")
#     )
#     decoder = Path(
#         os.getenv("SAM_DECODER_PATH", "models/mobilesam_int8/sam_vit_h_4b8939.decoder.quant.onnx")
#     )
#     backend = os.getenv("SAM_BACKEND", "ONNX")

#     for path in (encoder, decoder):
#         if not path.exists():
#             raise FileNotFoundError(f"Не найдена модель SAM: {path.resolve()}")
#     return encoder, decoder, backend

# @functools.cache
# def _bg_blur_module() -> BackgroundBlur:
#     """Создаётся при первом запросе размытия фона, а не при старте бота."""
#     encoder, decoder, backend = _sam_config()
#     logger.info("Загружаю SAM для bg_blur")
#     return BackgroundBlur(encoder, decoder, backend, kernel_size=BLUR_KERNEL_SIZE)

# @functools.cache
# def _bg_remove_module() -> BackgroundRemove:
#     encoder, decoder, backend = _sam_config()
#     logger.info("Загружаю SAM для bg_remove")
#     return BackgroundRemove(encoder, decoder, backend)

# def monochrome(image: np.ndarray) -> np.ndarray:
#     gray = _to_ndarray(_color(image, "BGR", "GRAY"))
#     return _to_ndarray(_color(gray, "GRAY", "BGR"))

# def negative(image: np.ndarray) -> np.ndarray:
#     return _to_ndarray(_inv(image))

# def blur(image: np.ndarray) -> np.ndarray:
#     return _to_ndarray(_blur(image))

# def bg_blur(image: np.ndarray) -> np.ndarray:
#     return _to_ndarray(_bg_blur_module()(image))

# def bg_remove(image: np.ndarray) -> np.ndarray:
#     return _to_ndarray(_bg_remove_module()(image))

# STYLES = {
#     "monochrome": monochrome,
#     "negative": negative,
#     "blur": blur,
#     "bg_blur": bg_blur,
#     "bg_remove": bg_remove,
# }

# def choose_style(text: str) -> str:
#     available = ", ".join(STYLES)
#     hint = f'Напишите, например: {{"style": "monochrome"}}. Доступные стили: {available}'

#     cleaned = text.strip()
#     for quote in "“”«»":
#         cleaned = cleaned.replace(quote, '"')

#     if not cleaned:
#         raise StyleError(f"Добавьте к фото описание обработки. {hint}")

#     try:
#         data = json.loads(cleaned)
#     except json.JSONDecodeError:
#         style = cleaned.lower()
#         if style in STYLES:
#             return style
#         raise StyleError(f"Не понял команду. {hint}") from None

#     if not isinstance(data, dict) or "style" not in data:
#         raise StyleError(f"Не понял команду. {hint}")

#     style = str(data["style"]).strip().lower()
#     if style not in STYLES:
#         raise StyleError(f"Неизвестный стиль «{style}». Доступные стили: {available}")
#     return style

# def apply_style(image: bytes, style: str) -> bytes:
#     array = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)

#     if array is None:
#         raise StyleError("Не удалось прочитать изображение")

#     array = _limit_size(array)
#     result = _ensure_bgr(_to_ndarray(STYLES[style](array)))

#     ok, encoded = cv2.imencode(".jpg", result, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])

#     if not ok:
#         raise RuntimeError("Не удалось закодировать результат в JPEG")

#     return encoded.tobytes()
