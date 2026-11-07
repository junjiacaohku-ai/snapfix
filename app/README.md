# SnapFix App（Flutter）

当前入口为 `lib/main.dart` 的 `SnapFixProductApp`，整合 FE-1 基础工程与 FE-2 产品交互。原 `lib/features/` 保留 W1 首页/扫描/预览骨架和对应测试，`lib/product/` 是当前产品 UI。

## 环境要求

- Flutter 3.47+ / Dart 3.13+
- Android Emulator 或 macOS + Xcode 的 iOS Simulator
- 相机/相册：`image_picker`
- 后端连接：`http`
- 系统分享：`share_plus`

## 启动后端

在项目根目录安装后端依赖并导入语料：

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -X utf8 corpus_store.py --database data/snapfix.db
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

无 key 时使用明确 mock；配置 `GEMINI_API_KEY` 后启用真实管线，`SNAPFIX_MOCK=1` 可强制离线。每条诊断的 `source_mode` 区分 mock、retrieval 和 gemini。

## 启动 Flutter

```bash
cd app
flutter pub get
flutter run
```

默认地址：

- Android Emulator：`http://10.0.2.2:8000`
- iOS Simulator：`http://127.0.0.1:8000`
- 真实手机：使用电脑局域网地址，手机的 `127.0.0.1` 不是电脑

可用 `--dart-define=SNAPFIX_API=http://<host>:8000` 覆盖。Android 仅 debug 配置允许课堂本地 HTTP。

## 当前流程

- 相机首页、相册、错误码输入和预览使用流程。
- 真实能力可用时，照片与错误码统一走 v1 API 并导入产品 UI；不可用时明确提示，不伪造识别。
- E24 型号未核实前建议专业处理；路由器等外部操作用于步骤反馈演示。
- 维修档案、维修状态、补充线索、双语报修、复制和系统分享调用。
- 原始照片不写入 SQLite，只保存文件名引用。
- 主题与 landing 统一：#0B1020 / #F5A623。

## 验证

```bash
flutter analyze
flutter test
flutter devices
flutter test integration_test -d <simulator-id>
```

`integration_test/app_flow_test.dart` 覆盖 W1 静态链路；`integration_test/product_flow_test.dart` 需要本机后端运行，覆盖产品预览 → 步骤反馈 → 报修真实 HTTP 链路。

当前集成分支在 iPhone 17 Pro / iOS 26.3 Simulator 上通过 7 项单元/Widget 测试和 2 项 iOS 集成测试。Android、真实手机拍照和系统分享仍需单独验收。
