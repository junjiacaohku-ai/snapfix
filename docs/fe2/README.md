# 杨蕊嘉 FE-2 W1/W2 交付与预览

本目录记录 FE-2 产品交互及其与 FE-1、BE-2、BE-1 的集成边界。新增代码主要位于 `app/lib/product/`、`server/ui_api.py` 和对应测试。真实图片诊断由团队 v1 管线负责，不由 FE-2 另建 provider。

## 当前行为

- 普通上传会验证真实图片，但只保存文件名引用，数据库不保存 base64 原图。
- 未接通真实诊断时显示“还在学习该维修技能中！”，不会按文件名偷偷进入样例。
- 正式输入和补充描述统一使用团队安全门；E24 预览在型号未核实前只建议专业处理。
- 显式“预览使用流程”可使用路由器等外部安全步骤体验反馈和报修，预览与正式记录隔离。
- 主题色与 `landing/index.html` 统一为深空蓝 #0B1020、琥珀 #F5A623。

`previews/` 是此前 Flutter Web 的视觉参考，其中 E24 四步样例和部分中文缺字已经不代表当前行为。最终视频和展示材料须重新从当前集成分支的模拟器录制。

## 本地浏览器运行

需要 Python 3.11+ 和 Flutter SDK。分别执行：

```sh
cd app
flutter pub get
flutter build web
```

```sh
# 在项目根目录，使用已安装后端依赖的 Python。
python server/run_fe2_preview.py
```

保持服务运行，打开 http://127.0.0.1:8000 。通过右上角唯一的“预览使用流程”入口查看演示。真实识别尚未接通时，普通上传会明确显示未支持，不会返回预设诊断。

## Android / iOS Simulator

```sh
python -m uvicorn main:app --app-dir server --port 8000
```

```sh
cd app
flutter run --dart-define=SNAPFIX_API=http://10.0.2.2:8000
```

iOS Simulator 默认 `http://127.0.0.1:8000`。真实手机需使用电脑局域网地址，拍照、系统分享和权限流程需单独验收。

## 检查

```sh
cd server
python -m pip install -r requirements-dev.txt
python -X utf8 -m pytest tests -q
```

```sh
cd app
flutter analyze
flutter test
```

数据库、密钥、构建目录和 APK 不提交 Git。贡献来源见 [contributions.md](contributions.md)，实际验证见 [validation.md](validation.md)。
