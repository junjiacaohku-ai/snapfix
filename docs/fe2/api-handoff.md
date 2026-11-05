# FE-2 接口交接

新增接口均位于 `/api/fe2`，原团队 `/api/sessions`、手册检索与旧报修端点保留。Flutter 和 React 使用同一份 Session JSON：设备字段、`mode`、`status`、`revisions`、`current_revision_index`、按对象和语言保存的 `reports`。这属于扩展契约，需要 FE-1 和后端在 PR 中共同复核，不声称全组已经批准。

| 动作 | 端点 | 关键行为 |
|---|---|---|
| 查询案例 | GET `/cases?q=&brand=&appliance=` | 只读，不建个人记录；当前为原型整理内容 |
| 案例适配 | POST `/cases/{id}/checks` | 同码不是适用证明，等待品牌和型号核对 |
| 正式错误码/描述 | POST `/diagnose` | `brand/category/model/error_code/note`；当前无真实 provider，保存输入并返回学习中 |
| 正式照片 | POST `/diagnose/photo` | multipart `file`；验证真实像素与5MB上限，保存实际选择的照片 |
| 预览场景 | POST `/demo` | `scenario=e24/router/billy/microwave`；只由流程预览入口进入 |
| 档案 | GET `/sessions?mode=live/demo`、GET/DELETE `/sessions/{id}` | 明确隔离两种记录，SQLite持久化，删除带走草稿/历史/反馈 |
| 维修状态 | PATCH `/sessions/{id}/status` | `investigating/awaiting_repair/resolved`，用户确认后改 |
| 步骤反馈 | POST `/sessions/{id}/steps/{step_id}/feedback` | `done/not_useful/skipped`；高风险禁止自行操作 |
| 补充线索 | POST `/sessions/{id}/follow-ups` | `note/photoUrl`至少一项，追加历史，不捏造新结论、不解除安全限制 |
| 报修草稿 | POST/PUT `/sessions/{id}/reports/{recipient}/{lang}` | 对象为`landlord/technician/after_sales`，语言`zh/en`；保存不自动改维修状态 |
| 重置模板 | GET `/sessions/{id}/reports/{recipient}/{lang}/template` | 返回新模板，不覆盖已保存草稿 |
| v1交接 | POST `/import/{legacy_id}` | 幂等导入团队诊断结果；当前旧管线为mock时拒绝，防止普通入口悄悄进入样例 |

## FE-1 接入

本地完整交付统一使用8051端口。小组服务若仍使用原来的8000端口，Android模拟器可通过 `flutter run --dart-define=SNAPFIX_API=http://10.0.2.2:8000` 指定地址，避免把服务端口差异误判为页面故障。独立Chrome调试需要后端允许对应本机Origin或使用同源代理；完整交付包的网页与API同源运行，无需另配。

团队真实管线接通、服务端正确报告非 mock 后，可将已有 v1 Session ID 交给新版：

```dart
Navigator.of(context).push(MaterialPageRoute<void>(
  builder: (_) => SnapFixProductApp(initialSessionId: response.id),
));
```

这是一个可独立运行的完整主题入口。若嵌入团队已有导航，可使用 `ProductHome(initialSessionId: response.id, api: sharedApi)`，并复用 `productTheme()`；不要在已有应用里重复创建数据库或保存模型密钥。FE-1 原页面保留在原目录；本 PR 的新版接口实现位于 `app/lib/product/api.dart`。

当前普通照片与错误码接口没有调用真实识别 provider；后端虽有团队检索接口，也不能据此宣传照片识别完成。导入时只使用后端实际返回字段，安全拒答会屏蔽全部步骤。来源区只展示实际提供的 snippet/来源字段，缺少原文时不补造引用；真实步骤与片段的绑定仍需要管线返回可靠数据。

## 模板与图片

演示内容提供人工核对的离线英文译文；任意新描述没有可靠译文时保留并标注原文未翻译。报修单只列实际反馈为已执行/无改善的操作，不凭空填写预约时间或故障配件。系统分享当前发送文本，实际照片需要发送者另附，未接平台派单。

服务按单机课堂版本设计，没有账号/多租户隔离。SQLite 中存有实际选择的照片，公开交付包排除运行数据库；不要把本机数据或模型密钥提交进仓库。
