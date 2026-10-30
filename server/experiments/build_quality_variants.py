"""Reproduce fixed image degradations; keep originals and attribution intact."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import PIL
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from image_quality import check_image

ASSETS = ROOT.parent / 'docs/demo-assets/public'
OUTPUT = ROOT.parent / 'docs/demo-assets/quality'
BRIGHTNESS_FACTOR = 0.15
BLUR_RADIUS = 12
FAMILIES = {
    'public-01.jpg': 'hayden-schiff-tl-wr740n',
    'public-02.jpg': 'hayden-schiff-tl-wr740n',
    'extra-3.jpg': 'hayden-schiff-tl-wr740n',
    'public-07.jpg': 'dinkun-chen-nn-gm333w',
    'extra-14.jpg': 'dinkun-chen-nn-gm333w',
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def make_preview(output, records):
    canvas = Image.new('RGB', (960, 870), '#f5f5f2')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    small = ImageFont.load_default(size=14)
    headers = ['Original', 'Brightness x 0.15', 'Gaussian blur: 12 px']
    for col, title in enumerate(headers):
        draw.text((col*320+16, 16), title, fill='#222222', font=font)
    chosen = ['public-01.jpg', 'public-03.jpg', 'public-05.jpg']
    for row, name in enumerate(chosen):
        paths = [ASSETS/name, output/(Path(name).stem+'-dark.png'), output/(Path(name).stem+'-blur.png')]
        for col, path in enumerate(paths):
            with Image.open(path) as image:
                thumb = ImageOps.contain(ImageOps.exif_transpose(image).convert('RGB'), (296, 220))
            canvas.paste(thumb, (col*320+12+(296-thumb.width)//2, 52+row*250+(220-thumb.height)//2))
        source = next(r for r in records if r['source_file']==name)
        draw.text((16, 278+row*250), f'{name} | {source["artist"]} | {source["license"]}', fill='#333333', font=small)
    draw.text((16, 809), 'Program-generated comparison; preview resized only. Inputs keep original dimensions.', fill='#333333', font=small)
    draw.text((16, 832), 'Composite: CC BY-SA 4.0. Original sources, licenses and parameters: manifest.json / README.md.', fill='#333333', font=small)
    canvas.save(output/'preview.png', compress_level=9)


def build(output=OUTPUT):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    sources = json.loads((ASSETS/'sources.json').read_text())
    seen, records, duplicates = {}, [], []
    for source in sources:
        name = source['file']
        if Path(name).name != name:
            raise ValueError('source filename must be local')
        if not name.endswith('.jpg'):
            continue
        data = (ASSETS/name).read_bytes()
        digest = sha256(data)
        if digest != source['sha256']:
            raise ValueError(f'original changed: {name}')
        if digest in seen:
            duplicates.append({'file':name, 'duplicate_of':seen[digest]})
            continue
        seen[digest] = name
        baseline = check_image(data).to_dict()
        record = dict(source_file=name, source_sha256=digest,
                      source_family=FAMILIES.get(name, digest), source_url=source['page'],
                      artist=source['artist'], license=source['license'],
                      license_url=source['license_url'], baseline=baseline, variants=[])
        with Image.open(ASSETS/name) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
            treatments = [
                ('dark', ImageEnhance.Brightness(image).enhance(BRIGHTNESS_FACTOR),
                 f'RGB channel brightness factor {BRIGHTNESS_FACTOR}; not physical camera exposure'),
                ('blur', image.filter(ImageFilter.GaussianBlur(BLUR_RADIUS)),
                 f'Pillow GaussianBlur radius {BLUR_RADIUS} pixels at original dimensions'),
            ]
            for kind, transformed, description in treatments:
                filename = Path(name).stem+'-'+kind+'.png'
                metadata = PngInfo()
                for key, value in {
                    'Source':source['page'], 'Author':source['artist'],
                    'License':source['license'], 'License URL':source['license_url'] or source['page'],
                    'Processing':description+'; EXIF orientation normalized; RGB; no resizing',
                }.items():
                    metadata.add_text(key, value)
                path = output/filename
                transformed.save(path, format='PNG', pnginfo=metadata, compress_level=9)
                record['variants'].append(dict(file=filename, kind=kind, sha256=sha256(path.read_bytes()),
                                               processing=description, expected_retake=True,
                                               blur_only_eligible=(kind=='blur' and baseline['accepted'])))
        records.append(record)
    manifest = dict(
        schema_version=1, python=platform.python_version(), pillow=PIL.__version__,
        generator_sha256=sha256(Path(__file__).read_bytes()),
        detector_sha256=sha256((ROOT/'image_quality.py').read_bytes()),
        parameters={'brightness_factor':BRIGHTNESS_FACTOR, 'gaussian_radius_px':BLUR_RADIUS,
                    'resize':False, 'orientation':'EXIF transpose', 'color_mode':'RGB',
                    'output':'lossless PNG', 'png_compress_level':9},
        thresholds_frozen_from='837a5369afc0aaaf738990a686dcb3aeff29095f',
        unique_originals=len(records), source_families=len({r['source_family'] for r in records}),
        variants=sum(len(r['variants']) for r in records), excluded_duplicates=duplicates,
        scope='Fixed severe degradations; related views share a family; no independent-sample accuracy claim',
        originals=records)
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    make_preview(output, records)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({k:result[k] for k in ['unique_originals','source_families','variants','parameters']}))
