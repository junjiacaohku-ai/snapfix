# SnapFix App(Flutter)

## 初始化(第一次,由 FE 同学执行)

本目录还没有 Flutter 工程。装好 Flutter SDK 后,在仓库根目录执行:

```bash
# 会提示目录非空(因为有本 README),选保留现有文件即可
flutter create --org hk.snapfix --project-name snapfix app/
cd app && flutter run
```

之后把 `flutter create` 生成的内容提交为第一个 `feat:` PR。

## 五屏骨架(W1 目标,对齐 PRD 第 7 节)

```
首页(扫描入口 + 档案入口 + 错误码速查入口)
├─ 扫描页 → 预览/质量检查 → 分析中(管线阶段动画)→ 诊断结果页
├─ 错误码速查页 → 诊断结果页
└─ 维修档案 → 历史详情(结果页只读)
```

底部 Tab:扫描 / 档案。主题:深空蓝底 + 琥珀色主行动色(色值见 landing/index.html 的 :root)。

## 对接后端

- 默认连 `http://127.0.0.1:8000`(本机 uvicorn);Android 模拟器用 `http://10.0.2.2:8000`
- 后端无 key 时自动 mock 模式,前端可全离线并行开发
- 契约以 `server/main.py` 为准;改契约前在群里喊一声(Git 规则)
