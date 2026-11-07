# SnapFix API 契约 v1（集成候选）

> 状态：三条后端分支已在本地集成，**待 FE-1、FE-2 确认后冻结**。冻结后改任何字段都须先在群内同步。
> 实现以 `server/main.py` 为准；本文档是前后端对齐依据。
> Base URL：本机/iOS Simulator `http://127.0.0.1:8000`；Android Emulator `http://10.0.2.2:8000`。

## 全局约定

- 响应使用 JSON；错误为 `{"detail":"..."}` 加相应 HTTP 状态码。
- 图片诊断目前为 mock，但响应对象与后续真实管线保持一致。
- `GET /api/health` 当前返回 `{"status":"ok","mock":true,"provider":"mock"}`。配置报修翻译 key 不会改变图片诊断状态。
- 空召回不是服务器错误：有效诊断请求返回 200，并明确说明无可用引用。

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
  "created_at": "ISO8601"
}
```

### Step

```json
{
  "id": "uuid",
  "idx": 1,
  "content": "操作说明",
  "citation_manual": "手册名",
  "citation_section": "PDF p.35",
  "feedback": "done | not_useful | skipped | null"
}
```

## 端点

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| POST | `/api/analyze/image` | multipart，字段名 `file` | Session；图片或演示场景无效时 422 |
| POST | `/api/diagnose/manual` | `{"brand":"Bosch","error_code":"E24"}` | Session；空白输入 422，数据库不可用 503 |
| POST | `/api/manuals/search` | ManualSearchRequest | 候选片段列表；数据库不可用 503 |
| GET | `/api/sessions` | — | Session[]，按时间倒序 |
| GET | `/api/sessions/{id}` | — | Session；不存在时 404 |
| DELETE | `/api/sessions/{id}` | — | `{"deleted":true}`；不存在时 404 |
| POST | `/api/sessions/{id}/steps/{step_id}/feedback` | `{"feedback":"done"}` | 更新后的 Session；非法反馈 422 |
| POST | `/api/sessions/{id}/report` | ReportRequest | `{"lang":"...","content":"报修文本"}` |
| GET | `/api/health` | — | 图片诊断 mock 状态 |

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

1. `safety_refused=true`：渲染安全拒答页，不渲染 steps，显示 `decision_reason` 和专业求助建议。
2. `decision`：`diy`、`landlord`、`professional` 三档决策，另有 `refused` 安全拒答。
3. `steps=[]`：可能是安全拒答、仅检索到候选资料或无引用；结合 `decision_reason` 展示，不能自行编造步骤。
4. 手动诊断无召回：200＋`professional`＋无引用说明，引导核对完整型号或联系售后。
5. 图片 422：展示返回的重拍/场景原因，允许重新选择图片或改用手动输入。
6. 网络失败：提示重试或离线演示，不白屏、不闪退。
7. 低置信度字段尚未加入 v1；后续新增时须保持向后兼容。

## 变更记录

- 2026-10-22：v1 草案（曹峻嘉）。
- W2 集成候选：E24 更正为洗碗机；加入检索端点、报修照片引用、空召回和错误行为；待 FE 确认冻结。
