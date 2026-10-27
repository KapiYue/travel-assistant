# 可编辑的行程草案

本阶段在完整的 `TravelRequest` 之后生成 `ItineraryDraft`。它只提供可编辑建议，不接入天气、路线、价格、营业时间、库存或预订工具；因此输出始终是 `draft`，所有活动均标记为 `unverified`。

## 职责划分

| 环节 | 职责 |
| --- | --- |
| Pydantic | 校验 `TravelRequest`、模型每日建议与 `ItineraryDraft` 的结构；拒绝非 `draft` 状态、非法天数、每日条目数量不符和日期不连续。 |
| 普通 Python | 复核需求完整性与 `missing_fields` 一致性；不完整时创建既有 `ClarificationPlan`；计算每日编号和日期；固定未验证提示；拒绝确认／预订承诺。 |
| 聊天模型 | 仅按目的地、人数、预算表达、偏好和限制，返回每天的主题及活动建议；不计算日期、状态或完整性。 |

模型输出没有日期、每日编号、行程状态或用户需求字段。程序会先建立日期骨架，再把验证后的建议放入骨架，因此模型无法改写目的地、出发日期、天数、人数、预算或限制。

## 使用方式

在 Python 中已经得到 `TravelRequest` 时，可调用：

```python
from backend.travel_assistant.itinerary import create_itinerary_draft

result = create_itinerary_draft(request)
```

完整需求会返回 `ItineraryDraft`；缺少目的地、出发日期、天数、人数或预算时，返回 `ClarificationPlan`，且不会创建或调用草案模型。模型配置缺失、调用失败、结构化输出非法、活动没有建议语义、每日数量错误，或含有“已确认”“已预订”等承诺时，流程会报出可行动错误，绝不返回部分行程。

命令行入口保持为：

```bash
python -m backend.travel_assistant "我和朋友两个人计划 2026 年 11 月 10 日去杭州玩 3 天，预算 5000 元，喜欢自然风景和慢节奏。"
```

该命令先展示 `travel_request` 和 `clarification_plan`；仅当需求完整时，才额外展示 `itinerary_draft`。运行命令需要模型配置；离线测试通过注入替代生成器验证，不依赖网络或密钥。

## 当前边界

- 草案可由调用方在其界面或业务层编辑，但本阶段不保存编辑内容，也不根据编辑重新规划。
- `notes` 明确说明景点开放、价格、路线、天气、库存和预订状态尚未核实。
- 后续接入旅行资料或实时工具后，仍须将工具结果和草案建议清楚区分，不能追溯性地把本阶段的建议改称为已确认事实。
