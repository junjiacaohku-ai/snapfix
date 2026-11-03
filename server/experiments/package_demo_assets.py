"""Export only the reviewed demo inputs and their attribution for teammates."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[2]
DIRECTORY = REPO / 'docs/demo-assets/alternatives'


def package(output):
    manifest = json.loads((DIRECTORY / 'manifest.json').read_text(encoding='utf-8'))
    files = []
    for item in manifest['assets']:
        source = (REPO / item['source_file']).resolve()
        name = item['demo_name']
        if Path(name).name != name or not source.is_relative_to(REPO.resolve()):
            raise ValueError('Invalid input path')
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f'Changed input: {name}')
        files.append((f'images/{name}', data))
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        for name, data in files:
            archive.writestr(name, data)
        archive.writestr('ATTRIBUTION.json', json.dumps(manifest['assets'], ensure_ascii=False, indent=2))
        archive.writestr('MANUAL-INPUTS.json', json.dumps(
            [case for case in manifest['cases'] if case['kind'] == 'manual'], ensure_ascii=False, indent=2))
        archive.writestr('README.txt',
            'SnapFix 演示输入包\n\nimages/ 中是18个可直接导入相册的文件；请同时保留ATTRIBUTION.json。\n'
            '路由器、BILLY、微波炉和洗碗机各3张公开照片，另有3张暗化和3张模糊图。\n'
            '这是离线演示素材，不是真实故障数据集。上传名选择mock场景，图片质量检查读取真实像素。\n'
            'E24优先使用MANUAL-INPUTS.json中的手动输入；洗碗机照片本身没有已确认的E24错误。\n'
            'S6复用router图片，反馈第一步后生成中英文草稿；手机分享仍需前端实测。\n'
            '来源、作者、许可、处理参数和校验值见ATTRIBUTION.json。\n'
            '完整说明与复跑脚本：https://github.com/junjiacaohku-ai/snapfix/pull/3\n')
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        for name, data in files:
            assert archive.read(name) == data
    return len(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    count = package(args.output)
    print(f'{count} images with attribution exported to {args.output}')
