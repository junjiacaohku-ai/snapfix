# SnapFix App（Flutter）

W1 已完成 Flutter 双端工程初始化，以及 FE-1 负责的 **首页 → 扫描 → 预览** 静态主链路。

## 环境要求

- Flutter 3.47.5 / Dart 3.13.4（当前开发环境）
- Android SDK 36（Windows 队友使用 Android Emulator）
- iOS 构建需在 macOS + Xcode 环境执行
- 相机/相册依赖 `image_picker 1.2.4`，权限声明已补齐

## 安装与运行

```bash
cd app
flutter pub get
flutter run
```

指定 Android 模拟器：

```bash
flutter emulators
flutter emulators --launch Medium_Phone
flutter run -d emulator-5554
```

## 本地验证

```bash
flutter analyze
flutter test
flutter test integration_test -d emulator-5554
# macOS + Xcode：先用 flutter devices 查询 iOS Simulator ID
flutter test integration_test -d <ios-simulator-id>
```

W1 验收路径：首页点击 **拍照诊断** → 扫描页 → **使用演示照片** → 预览页。相机与相册按钮走真实 `image_picker`；无可用媒体时可用演示照片完成静态链路验收。

集成分支已在 Flutter 3.47.7、iPhone 17 Pro / iOS 26.3 Simulator 复测：静态检查 0 issues、2 项 Widget 测试和 1 项 iOS 集成测试通过。该结果只覆盖 W1 静态链路，不代表真实诊断 API、档案或报修流程已完成。

## 当前页面

- 首页：扫描入口、错误码入口、维修档案入口
- 扫描页：相机、相册、演示照片入口
- 预览页：照片预览、质量提示、隐私说明、W2 衔接点
- 档案/错误码：仅入口与占位，分别留给 FE-2 与 W2 接入

## 对接后端

- 默认本机：`http://127.0.0.1:8000`
- Android Emulator：`http://10.0.2.2:8000`
- 后端无 key 时自动 mock，前端可并行开发
- 契约以 `server/main.py` 为准；改契约前先在群里同步
