# SnapFix App（Flutter）

当前入口为 `lib/main.dart` 的 `SnapFixProductApp`，整合 FE-1 基础工程与 FE-2 产品交互。原 `lib/features/` 保留 W1 首页/扫描/预览骨架和对应测试，`lib/product/` 是当前产品 UI。

## 1. 首次准备

默认已有 VS Code、Git 和浏览器。请先按 [根 README](../README.md) 检查 Python、Flutter，已有则跳过安装，再获取源码及导入语料。本文件所有 Flutter 命令在 `app` 目录执行；后端命令在 `server` 执行，已经在子目录则不要重复 `cd app` 或 `cd server`。

- 建议 Flutter 3.47.9；`pubspec.yaml` 要求 Dart `^3.13.4`，Dart 随 Flutter SDK 安装。
- 推荐使用已有浏览器体验，本地网页无需 Xcode、Android Studio 或手机模拟器。手机运行章节面向已配置对应工具链的用户，无需重复下载。
- `flutter --version` 验证 SDK；`flutter doctor` 检查目标平台。只运行网页时可以暂缓 Android/Xcode 警告。
- 依赖：`image_picker` 提供相机/相册，`http` 连接 API，`share_plus` 调用系统分享；用 `flutter pub get` 统一安装，不需要逐项安装。

## 2. 浏览器快速体验（Windows / macOS）

先按根 README 配置好后端环境和语料，但暂不启动 Uvicorn。在终端 B 的 `app` 目录编译：

```bash
flutter pub get
flutter build web
```

看到 `Built build/web` 后，回到终端 A 的 `server` 目录启动网页与 API 共用的服务。

macOS（先前已激活 `.venv`）：

```bash
python run_fe2_preview.py
```

Windows PowerShell（不需要激活脚本）：

```powershell
.\.venv\Scripts\python.exe run_fe2_preview.py
```

保持终端 A 运行，Chrome 打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。点击“预览使用流程”并选择路由器，可体验反馈、报修及档案。不要双击构建出的 HTML，也不要同时运行另一个占用 8000 的 Uvicorn。

网页不等于手机端验收；手机相机、权限、系统分享需要按下一节验证。修改 Flutter 界面后需重新构建网页；改 README 不需要重新构建。

## 3. 手机应用编译与运行

本节假设已有可用的 Android 或 iOS 模拟器；未配置时先使用浏览器版，本文件不再列出平台工具下载步骤。先停止上节预览服务（终端 A 按 `Ctrl + C`），在同一 `server` 目录启动 API。

macOS（已激活 `.venv`）：

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

另一个终端在 `app` 目录执行，两种系统相同：

```bash
flutter pub get
flutter devices
```

打开对应模拟器，并将下面的 `DEVICE_ID` 替换为列出的设备 ID。`flutter run` 会编译、安装并启动 App。

Android Emulator（Windows 或 macOS）：

```bash
flutter run -d DEVICE_ID --dart-define=SNAPFIX_API=http://10.0.2.2:8000
```

iOS Simulator（仅 macOS）：

```bash
flutter run -d DEVICE_ID --dart-define=SNAPFIX_API=http://127.0.0.1:8000
```

仅编译 Android 调试包（两种系统相同）：

```bash
flutter build apk --debug --dart-define=SNAPFIX_API=http://10.0.2.2:8000
```

输出：`app/build/app/outputs/flutter-apk/app-debug.apk`。此包配置模拟器后端地址，不能直接用于其他电脑或真实手机。

仅编译 iOS 模拟器版本（macOS）：

```bash
flutter build ios --simulator --debug --dart-define=SNAPFIX_API=http://127.0.0.1:8000
```

输出目录：`app/build/ios/iphonesimulator/`。真实 iPhone 另需签名与设备配置。

### 后端地址

| 运行位置 | 后端地址 |
|---|---|
| 本机浏览器预览 | 使用当前网页 origin，与 API 同为 `http://127.0.0.1:8000` |
| Android Emulator | `http://10.0.2.2:8000` |
| iOS Simulator | `http://127.0.0.1:8000` |
| 真实手机 | 电脑局域网 IP，如 `http://192.168.1.20:8000` |

真实手机需要与电脑网络互通，API 改为 `--host 0.0.0.0` 并允许相应防火墙连接；App 构建时传入电脑 IP。手机自己的 `127.0.0.1` 不是电脑。Android 本地 HTTP 仅在 debug 配置允许；iOS 本地网络权限、HTTP 策略及系统分享还需实机验证。

## 4. 当前流程与限制

- 相机首页、相册、错误码输入和预览使用流程。
- `GEMINI_API_KEY` 仅配置在后端，未强制 mock 时打开在线能力；App 自身不保存 key。在线照片走 v1 API 再导入产品档案，无在线能力时照片仅验证格式/大小并保存待处理记录。
- 当前手动错误码只有在在线能力开启且补充描述为空时走 v1；无 key 时 App 不调用本地 BM25，但可在后端 `/docs` 单独验收该检索。此限制未在本次文档修改中修复。
- E24 型号未核实前建议专业处理；路由器等外部操作用于步骤反馈演示。
- App 报告列出“完成”和“没用”步骤并区分状态，不包含“跳过”。演示有内置英文译文；其他中文可能保留为注明未翻译的原文，App 不使用 v1 报告的在线翻译。照片文件名暂不进入 App 报告正文，英文模板也未完整包含设备类别，发送时需另附实际照片。
- 首次生成的草稿会保留以保护编辑内容；反馈或补充线索改变后，如需更新文案，使用恢复模板功能并保存。
- App 档案存于 `fe2_sessions`；导入 v1 的记录是副本。App 反馈不会同步到 v1，App 删除也不删除 v1 原始诊断。演示与正式档案分开显示。
- 原始照片不写入 SQLite，只保存文件名引用。
- 主题与 landing 统一：#0B1020 / #F5A623。

## 5. 验证

在 `app` 目录执行（Windows / macOS 相同）：

```bash
flutter analyze
flutter test
flutter devices
flutter test integration_test -d DEVICE_ID
```

`DEVICE_ID` 替换为实际模拟器 ID。`integration_test/app_flow_test.dart` 覆盖 W1 静态链路；`integration_test/product_flow_test.dart` 需要本机后端运行，覆盖产品预览 → 步骤反馈 → 报修 HTTP 链路。Android 测试如需覆盖默认测试地址，可附加 `--dart-define=SNAPFIX_API=http://10.0.2.2:8000`。

既有集成验证记录报告 iPhone 17 Pro / iOS 26.3 Simulator 上通过 7 项单元/Widget 测试和 2 项 iOS 集成测试；这不是本次 README 修改后重新运行的结果。Android、真实手机拍照和系统分享仍需单独验收。记录实际系统、设备、Flutter 版本和输出，不能用后端测试通过代替手机验收。

找不到 Flutter、8000 端口占用或网页 404，请查 [根 README 的常见问题](../README.md#14-常见问题)。
