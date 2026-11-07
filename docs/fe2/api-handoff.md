# FE-2 接口交接

`/api/fe2` 是产品 UI 扩展契约，原团队 `/api/sessions`、手册检索和报修端点保留。Flutter 使用包含设备字段、`mode`、`status`、`revisions`、`current_revision_index` 和按对象/语言保存的 `reports` 的 UI Session JSON。扩展字段须与 `docs/api-contract.md` 一起复核，不视为全组已批准的替代数据模型。

| 动作 | 端点 | 关键行为 |
|---|---|---|
| 查询案例 | GET `/cases?q=&brand=&appliance=` | 只读，不建个人记录；当前为原型整理内容 |
| 案例适配 | POST `/cases/{id}/checks` | 同码不是适用证明，等待品牌和型号核对 |
| 正式错误码/描述 | POST `/diagnose` | 统一安全门检查；真实 provider 未接通时保存输入并返回学习中或拒答 |
| 正式照片 | POST `/diagnose/photo` | multipart `file`；验证真实像素与 5MB 上限，只保存文件名引用，不保存原图 |
| 预览场景 | POST `/demo` | `scenario=e24/router/billy/microwave`；只由流程预览入口进入 |
| 档案 | GET `/sessions?mode=live/demo`、GET/DELETE `/sessions/{id}` | 隔离预览与正式记录，SQLite 持久化 |
| 维修状态 | PATCH `/sessions/{id}/status` | `investigating/awaiting_repair/resolved`，用户确认后修改 |
| 步骤反馈 | POST `/sessions/{id}/steps/{step_id}/feedback` | `done/not_useful/skipped`；高风险禁止自行操作 |
| 补充线索 | POST `/sessions/{id}/follow-ups` | `note/photo_ref` 至少一项；追加历史并重新检查安全门，只保存文件名 |
| 报修草稿 | POST/PUT `/sessions/{id}/reports/{recipient}/{lang}` | `landlord/technician/after_sales`，`zh/en`；保存不自动改状态 |
| 重置模板 | GET `/sessions/{id}/reports/{recipient}/{lang}/template` | 返回新模板，不覆盖已保存草稿 |
| v1 交接 | POST `/import/{legacy_id}` | 幂等导入团队诊断结果；旧图片管线为 mock 时拒绝导入 |

## 安全与隐私

- 正式诊断、演示生成和补充描述统一调用 `safety_gate.py`，不再使用 FE-2 私有高危关键词表。
- E24 预览只展示候选资料和专业处理建议；实际型号未核实，不提供四步拆装指导。步骤反馈演示使用路由器等外部安全操作。
- `photo_refs` 和 `supplementary_photo_ref` 只是文件名。`photoUrl`、base64 图片和远程图片地址不再接受或保存。
- 报修发送文本，实际照片由发送者另附；数据库不包含用户原始照片。

## 本地连接与 FE-1 接入

团队服务统一使用 8000 端口。Android 模拟器默认 `http://10.0.2.2:8000`，iOS Simulator 默认 `http://127.0.0.1:8000`，也可用 `SNAPFIX_API` 覆盖。独立 Chrome 调试需要后端允许本机 Origin 或使用同源代理。

真实管线接通后，可将 v1 Session ID 交给新版：

```dart
Navigator.of(context).push(MaterialPageRoute<void>(
  builder: (_) => SnapFixProductApp(initialSessionId: response.id),
));
```

也可嵌入 `ProductHome(initialSessionId: response.id, api: sharedApi)` 并复用 `productTheme()`。FE-1 原页面保留作基础参考，实际入口以 `app/lib/main.dart` 为准。

演示内容提供人工核对的离线英文译文；任意新描述没有可靠译文时保留并标注原文未翻译。报修单只列实际反馈，不凭空填写预约时间或故障配件。服务按单机课堂版本设计，没有账号或多租户隔离；运行数据库、密钥和构建目录不提交 Git。
