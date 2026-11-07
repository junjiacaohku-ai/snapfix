"""Conservative image checks; device recognition remains a separate step."""
from dataclasses import asdict, dataclass
from io import BytesIO
import warnings
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000


@dataclass(frozen=True)
class QualityResult:
    accepted: bool
    reason: str
    width: int = 0
    height: int = 0
    brightness: float | None = None
    sharpness: float | None = None

    def to_dict(self):
        return asdict(self)


def check_image(data: bytes) -> QualityResult:
    if not data or len(data) > MAX_BYTES:
        return QualityResult(False, '请选择不超过10MB的图片。')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                width, height = source.size
                if width * height > MAX_PIXELS:
                    return QualityResult(False, '图片尺寸过大，请压缩后重试。', width, height)
                if min(width, height) < 160:
                    return QualityResult(False, '图片分辨率太低，请靠近设备重新拍摄。', width, height)
                # Orientation is used for measurement only; nothing is saved.
                gray = ImageOps.exif_transpose(source).convert('L')
                gray.thumbnail((512, 512))
                if min(gray.size) < 3:
                    return QualityResult(False, '图片过窄，请拍摄完整设备或面板。', width, height)
                pixels = np.asarray(gray, dtype=np.float32)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        return QualityResult(False, '无法读取图片，请上传有效图片。')
    brightness = float(pixels.mean())
    laplace = (-4 * pixels[1:-1, 1:-1] + pixels[:-2, 1:-1] + pixels[2:, 1:-1]
               + pixels[1:-1, :-2] + pixels[1:-1, 2:])
    sharpness = float(laplace.var())
    if brightness < 35:
        reason = '照片过暗，请补光后重拍。'
    elif sharpness < 12:
        reason = '照片细节不清，请对焦并靠近设备重拍。'
    else:
        reason = ''
    return QualityResult(not reason, reason, width, height,
                         round(brightness, 2), round(sharpness, 2))
