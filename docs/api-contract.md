# SnapFix API 契约 v1(冻结草案)

> 状态:**待 FE 确认后冻结**(W1 截止 10/28)。冻结后改任何字段=改契约,群里先喊再动。
> 实现以 `server/main.py` 为准;本文档是前后端唯一对齐依据。
> Base URL:本机 `http://127.0.0.1:8000`;Android 模拟器用 `http://10.0.2.2:8000`。

## 全局约定

- 所有响应 JSON;错误为 `{"detail": "..."}` + HTTP 状态码(404 等)
- 无 API key 时后端为 mock 模式,响应结构与真管线**完全一致**,前端无需感知
- `GET /api/health` → `{"status":"ok","mock":true|false,"provider":"mock"|"gemini"}`

## 核心对象

### Session(诊断会话)

```json
{
  "id": "uuid",
  "device_category": "washing_machine",
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

### Step(分步指导,挂在 Session 里)

```json
{
  "id": "uuid",
  "idx": 1,
  "content": "操作说明",
  "citation_manual": "手册名",
  "citation_section": "§7.2",
  "feedback": "done | not_useful | skipped | null"
}
```

## 端点

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| POST | `/api/analyze/image` | multipart,字段名 `file`(照片) | Session |
| POST | `/api/diagnose/manual` | `{"brand":"Bosch","error_code":"E24"}` | Session |
| GET | `/api/sessions` | — | Session[](按时间倒序) |
| GET | `/api/sessions/{id}` | — | Session(404 若不存在) |
| DELETE | `/api/sessions/{id}` | — | `{"deleted":true}`(404 若不存在) |
| POST | `/api/sessions/{id}/steps/{step_id}/feedback` | `{"feedback":"done"}` | 更新后的 Session |
| POST | `/api/sessions/{id}/report` | `{"lang":"zh"|"en"}` | `{"lang":"...","content":"报修文本"}` |
| GET | `/api/health` | — | 见上 |

## 前端必须处理的业务态

1. **`safety_refused=true`** → 渲染安全拒答页(红/警示色),**不渲染 steps**(此时 steps 必为空),显示 decision_reason + 建议找师傅
2. **`decision` 三档**(diy/landlord/professional)→ 决策卡 UI,各配一句话理由
3. **`confidence` 低**(后续版本加入)→ 引导用户走 `/api/diagnose/manual` 手动输入
4. **网络失败** → 提示"演示模式/重试",不白屏不闪退

## 变更记录

- 2026-10-22 v1 草案(曹峻嘉),待 FE 确认冻结
