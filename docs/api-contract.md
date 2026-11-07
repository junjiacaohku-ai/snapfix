# SnapFix API 契约 v1（集成候选）

> 状态：后端、FE-1、FE-2 已在本地集成分支整合，**待 FE-1、FE-2 正式 review 后冻结**。冻结后改任何字段都须先在群内同步。
> 实现以 `server/main.py` 为准；FE-2 的 UI 扩展字段另见 `docs/fe2/api-handoff.md`。
> Base URL：本机/iOS Simulator `http://127.0.0.1:8000`；Android Emulator `http://10.0.2.2:8000`。

## 全局约定

- 响应使用 JSON；错误为 `{"detail":"..."}` 加相应 HTTP 状态码。
- 无 key 时图片诊断为 mock；配置 `GEMINI_API_KEY` 后启用真实管线，`SNAPFIX_MOCK=1` 可强制离线演示。
- `GET /api/health` 返回当前配置：`{"status":"ok","mock":true|false,"provider":"mock"|"gemini"}`。它表示配置，不保证每次在线调用都成功。
- 每个 Session 用 `source_mode` 区分 `mock`、`retrieval`、`gemini`，前端不得把 mock 结果标成真实识别。
- 空召回不是服务器错误：有效诊断请求返回 200，并明确说明无可用引用。
- 原始照片不写入 SQLite；报修和续诊只保存文件名引用。

## 核心对象

### Session

```json
{
  "id": "uuid",
  "device_category": "dishwasher",
  "brand": "Bosch | null",
  "model": "string | null",
  "error_code": "E24 | null",
  "decision": "diy | landlord | professional | refused",
  "decision_reason": "一句话理由",
  "safety_refused": false,
  "steps": ["Step..."],
  "created_at": "ISO8601",
  "source_mode": "mock | retrieval | gemini"
}
```

### Step

```json
{
  "id": "uuid",
  "idx": 1,
  "content": "操作说明",
  "citation_manual": "手册名",
  "citation_section": "PDF p.35 · chunk-id",
  "feedback": "done | not_useful | skipped | null"
}
```

真实生成步骤必须引用检索返回的 chunk。无法映射、引用伪造或安全校验失败的步骤会被丢弃；没有有效引用时不展示 DIY 步骤。

## 端点

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| POST | `/api/analyze/image` | multipart，字段名 `file` | Session；图片无效时 422，数据库不可用 503 |
| POST | `/api/diagnose/manual` | `{"brand":"Bosch","error_code":"E24"}` | Session；空白输入 422，数据库不可用 503 |
| POST | `/api/manuals/search` | ManualSearchRequest | 候选片段列表；数据库不可用 503 |
| GET | `/api/sessions` | — | Session[]，按时间倒序 |
| GET | `/api/sessions/{id}` | — | Session；不存在时 404 |
| DELETE | `/api/sessions/{id}` | — | `{"deleted":true}`；不存在时 404 |
| POST | `/api/sessions/{id}/steps/{step_id}/feedback` | `{"feedback":"done"}` | 更新后的 Session；非法反馈 422 |
| POST | `/api/sessions/{id}/report` | ReportRequest | `{"lang":"...","content":"报修文本"}` |
| GET | `/api/health` | — | 当前 mock/provider 配置 |

### 图片诊断与降级

真实管线顺序：图片质量门 → Gemini 视觉提取 → 归一化 → BM25 → 安全门 → 结构化生成 → 引用校验。

- 视觉或生成调用失败时，v1 可回退到文件名对应的明确 mock 场景，`source_mode` 必须为 `mock`。
- 真实调用成功时 `source_mode` 为 `gemini`。
- 低置信度、空召回、型号未核实或无有效引用时返回 `professional` 和空步骤，不编造维修指导。
- 高危结果返回 `refused`、`safety_refused:true` 和空步骤。
- 未知图片且没有可用真实结果或 mock 场景时返回 422。

### ManualSearchRequest

```json
{
  "query": "Bosch E24 排水",
  "category": "",
  "category_hint": "dishwasher",
  "brand": "Bosch",
  "error_code": "E24",
  "manual_id": "",
  "limit": 3
}
```

- `query` 必填，1–500 字符；`limit` 为 1–10，默认 3。
- `category`、`brand`、`error_code`、`manual_id` 是严格筛选；`category_hint` 只加权，不过滤。
- 响应：`{"matched":true|false,"matches":[...],"message":"..."}`。
- 每个 match 至少包含 `id`、`manual_id`、`content`、`page`、`source_url`、`score` 和 `score_detail`。
- 无匹配返回 200、`matched:false`、`matches:[]`，不回退成其他错误码。

### ReportRequest

```json
{
  "lang": "zh | en",
  "photo_refs": ["device-front.jpg"]
}
```

- `lang` 默认 `zh`；`photo_refs` 可省略，最多 5 个非空字符串。
- 只把 `feedback == "done"` 的步骤写入报修。
- 照片引用只是文字，发送时仍需另附实际照片。
- 英文在线翻译不可用时仍返回 200 和基础英文报告，并注明步骤正文未翻译。

## 前端必须处理的业务态

1. `source_mode=mock`：明确标注离线演示，不能作为真实识别准确率证据。
2. `safety_refused=true`：渲染安全拒答页，不渲染 steps，显示 `decision_reason` 和专业求助建议。
3. `decision`：`diy`、`landlord`、`professional` 三档决策，另有 `refused` 安全拒答。
4. `steps=[]`：可能是安全拒答、仅检索到候选资料、低置信度或无引用；结合 `decision_reason` 展示。
5. 手动诊断无召回：200＋`professional`＋无引用说明，引导核对完整型号或联系售后。
6. 图片 422：展示返回的重拍/场景原因，允许重新选择图片或改用手动输入。
7. 网络失败：提示重试或离线演示，不白屏、不闪退，不静默把失败结果换成真实诊断。
8. 低置信度数值字段尚未加入 v1；后续新增时须保持向后兼容。

## 变更记录

- 2026-10-22：v1 草案（曹峻嘉）。
- W2 集成候选：E24 更正为洗碗机；加入检索端点、报修照片引用、空召回和错误行为。
- W3 集成候选：加入 `source_mode`、真实管线、引用校验、强制 mock 开关和原图不落盘约定；待 FE 正式确认。
