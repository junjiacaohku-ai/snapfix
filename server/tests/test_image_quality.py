from io import BytesIO
from pathlib import Path
from PIL import Image
from image_quality import MAX_BYTES, check_image


def test_valid_and_dark_public_photos():
    assets = Path(__file__).resolve().parents[2] / 'docs/demo-assets/public'
    assert check_image((assets/'public-01.jpg').read_bytes()).accepted
    dark = check_image((assets/'public-09.jpg').read_bytes())
    assert not dark.accepted and '过暗' in dark.reason


def test_invalid_and_oversized_uploads():
    assert not check_image(b'invalid').accepted
    assert not check_image(b'x' * (MAX_BYTES + 1)).accepted


def test_resolution_and_featureless_fixture():
    # Synthetic unit fixtures, not collected photos or experiment observations.
    small = BytesIO()
    Image.new('RGB', (32,32), 'white').save(small, format='PNG')
    assert '分辨率' in check_image(small.getvalue()).reason
    blank = BytesIO()
    Image.new('RGB', (512,512), 'gray').save(blank, format='PNG')
    assert '细节' in check_image(blank.getvalue()).reason
