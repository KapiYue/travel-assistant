# 缺失信息追问：四层职责边界

本阶段只决定还需要问什么、如何问。它不会根据回答修改需求，不保存多轮状态，也不会生成行程、推荐或实时事实。

## 模型：只理解自然语言

LangChain 的 Structured Output 仍只服务于上一阶段的旅行需求提取。模型只提取用户明确表达的字段，不能因为“带父母”推测人数，也不能补写日期、预算或偏好。

## Pydantic：拒绝不合法的需求

`TravelRequest` 在进入追问规则前已经过 Pydantic 校验：天数和人数必须大于零，日期必须合法。`ClarificationQuestion` 与 `ClarificationPlan` 也有明确的数据结构，避免输出混杂任意文本。

## 普通 Python：计算缺失字段

`TravelRequest.missing_fields` 由程序按固定顺序计算：`destination`、`start_date`、`days`、`traveler_count`、`budget`。偏好和限制允许为空，不会触发追问。

## 普通 Python：生成追问计划

`create_clarification_plan()` 只接受已校验且状态一致的 `TravelRequest`。它会检查 `missing_fields` 是否仍与需求本身匹配，然后为每个缺失字段生成一条固定的中文问题和原因。未知、重复或不一致字段会明确报为规则层错误，且不会返回部分问题。

完整需求的计划没有问题，消息为“信息已齐全，可以进入后续阶段。”；不完整需求只说明仍需补充信息。整个计划生成过程不调用聊天模型，因此已有有效需求时不依赖模型配置。

## 本地运行

```bash
python -m backend.travel_assistant "想带父母去杭州轻松玩，最好多看看自然风景。"
```

该命令先执行需求提取，再显示 `travel_request` 和 `clarification_plan`。前一步需要模型配置；如果已经在 Python 中获得有效的 `TravelRequest`，可直接调用 `create_clarification_plan()`，无需模型或网络。
