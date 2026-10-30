# 六场景演示和验收

这份包可复跑后端离线演示。原图、来源、处理图、预期结果都在仓库中；E24走手动输入，暂没有经过核实的故障照片。手机端验收另记，不把接口结果当作手机截图。

## 换电脑复跑

先安装Python 3.11或更新版本。复制完整源码包并解压，保留 `docs/` 和 `server/` 的相对位置。在 `server/` 打开终端：

```sh
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows：第一行用 python -m venv .venv，激活用 .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python experiments/run_acceptance.py --label demo-main --output ../demo-main.json
```

备用机最后一行改成 `--label demo-backup --output ../demo-backup.json`。安装依赖需要网络，安装后六场景检查不访问模型或互联网。看到 `6/6` 和 `mock health: True` 才算本次后端检查通过。脚本先核对图片哈希，用临时数据库运行，不清空已有档案。

两份结果必须来自两台实际电脑；在同一台电脑运行两次不算双机验证。此次已在本机复跑，备用机结果待补。服务的实际启动和重启检查见 `server/experiments/server-check.json`。

## 场景与预期

| 场景 | 输入 | 预期结果 |
|---|---|---|
| S1 路由器 | `public/public-01.jpg`，上传名 `router.jpg` | 外部检查步骤，型号未确认；原图不证明红灯故障 |
| S2 洗碗机 E24 | 手动输入 `Bosch` + `E:24` | 洗碗机、转专业处理、型号为空 |
| S3 BILLY | `public/public-03.jpg`，上传名 `billy.jpg` | 含防倾倒提醒的步骤；原图是外观示例 |
| S4 微波炉 | `public/public-05.jpg`，上传名 `microwave.jpg` | 拒答，步骤为空 |
| S5 重拍 | `public/public-09.jpg`，任意上传名 | 422，提示重拍；另可用 `quality/` 的处理图复测 |
| S6 报修 | 完成S1的第一步，生成中文和英文报修 | 草稿包含已尝试步骤，提示发送者另附照片 |

图片路径相对 `docs/demo-assets/`。精确输入和校验值见 `demo-assets/demo-manifest.json`，作者和许可见 `demo-assets/public/sources.json`。接口耗时是本机测试客户端耗时，不是手机端延迟。

## 手机联调时记录

每项保留：App版本／后端提交、手机型号、输入文件、页面截图、实际结果、从操作到显示结果的耗时。不能只拍“通过”字样。

- S1–S4：拍摄或相册选择 → 结果 → 步骤／引用；E24另检查手动输入。
- S5：暗图和模糊图各一次，确认重拍后能回到拍摄页。
- S6：步骤反馈 → 中英文报修 → 复制／系统分享；再检查档案读取、删除和重启。
- 断网后切入演示模式，重新跑关键流程。实际识别结果与演示模式分开保存。

## 五分钟彩排

| 时间 | 内容 |
|---|---|
| 0:00–0:30 | 租房报修问题与应用用途 |
| 0:30–1:20 | 手动输入洗碗机E24，说明型号不明时的处理 |
| 1:20–2:20 | BILLY步骤和来源 |
| 2:20–3:00 | 微波炉安全拒答 |
| 3:00–4:20 | 步骤反馈、双语报修、复制或分享 |
| 4:20–5:00 | 档案与总结 |

正式彩排两遍，各记录实际总耗时、卡住的位置、负责人和复测结果。上表是计划，不是彩排记录。11月19日前由全组确认演示机、备用机和预录视频。
