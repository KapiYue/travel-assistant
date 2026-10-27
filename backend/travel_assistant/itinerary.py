"""生成并校验可编辑旅行草案的受控流程。"""

from __future__ import annotations

import os
from datetime import timedelta
from typing import Any, Protocol

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.travel_assistant.clarification import ClarificationPlanError, create_clarification_plan
from backend.travel_assistant.models import (
    ActivitySuggestion,
    ClarificationPlan,
    DailyItineraryItem,
    ItineraryDraft,
    TravelRequest,
    calculate_missing_fields,
)


ITINERARY_SYSTEM_PROMPT = """你是旅行草案建议器，只返回符合结构化 schema 的每日建议。

你只能依据提供的目的地、偏好、限制、预算表达和人数提出可编辑建议。
每一天必须给出一个主题和至少一项活动建议，活动说明使用“建议”“可考虑”等语气。
不得计算日期、天数、每日编号、草案状态或缺失字段；这些全部由程序处理。
不得声称景点开放、路线可用、价格准确、天气适宜、名额可用，或任何内容已确认、已预订。
不得提供精确票价、实时营业时间、预订链接或虚构来源。所有动态信息均尚未核实。"""

# 这些词表示未经工具支持的确认承诺；发现后会拒绝整个模型输出。
FORBIDDEN_COMMITMENT_TERMS = ("已确认", "已预订", "已订", "confirmed", "booked")
SUGGESTION_TERMS = ("建议", "可考虑", "可安排")


class ItineraryDraftError(ValueError):
    """草案规则层无法安全生成完整结果时抛出。"""


class ItineraryModelConfigurationError(RuntimeError):
    """生成草案所需的本地模型配置缺失时抛出。"""


class ItineraryModelInvocationError(RuntimeError):
    """模型调用失败且没有可返回的完整草案时抛出。"""


class ItineraryStructuredOutputError(RuntimeError):
    """模型建议不符合草案 schema 或安全规则时抛出。"""


class DailySuggestion(BaseModel):
    """模型可返回的一天建议，不包含程序控制的日期和编号。"""

    model_config = ConfigDict(extra="forbid")

    theme: str = Field(min_length=1, description="当天的可编辑建议主题。")
    activities: list[ActivitySuggestion] = Field(
        min_length=1,
        description="当天的未验证活动建议。",
    )


class ItinerarySuggestions(BaseModel):
    """模型输出的全部每日建议，日期骨架由程序后续附加。"""

    model_config = ConfigDict(extra="forbid")

    daily_suggestions: list[DailySuggestion] = Field(
        min_length=1,
        description="按旅行日顺序排列的每日建议。",
    )


class StructuredItineraryGenerator(Protocol):
    """草案流程需要的最小模型调用接口。"""

    def invoke(self, input_value: dict[str, object]) -> Any:
        """返回每日建议的结构化结果。"""


def create_structured_itinerary_generator() -> StructuredItineraryGenerator:
    """建立仅生成每日建议的 Structured Output 模型入口。"""
    load_dotenv()
    api_key = os.getenv("DATA_API_KEY") or os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("DATA_MODEL") or os.getenv("OPENAI_MODEL")
    base_url = os.getenv("DATA_BASE_URL") or os.getenv("OPENAI_BASE_URL") or None

    if not api_key or not model_name:
        raise ItineraryModelConfigurationError(
            "缺少模型配置。请复制 .env.example 为 .env，并填写 DATA_API_KEY 和 DATA_MODEL。"
        )

    prompt = ChatPromptTemplate.from_messages(
        [("system", ITINERARY_SYSTEM_PROMPT), ("human", "{request_context}")]
    )
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )
    return prompt | llm.with_structured_output(ItinerarySuggestions)


def create_itinerary_draft(
    request: TravelRequest,
    generator: StructuredItineraryGenerator | None = None,
) -> ItineraryDraft | ClarificationPlan:
    """为完整需求生成草案；不完整需求仅返回既有追问计划。"""
    _validate_request_for_draft(request)
    try:
        clarification_plan = create_clarification_plan(request)
    except ClarificationPlanError as error:
        raise ItineraryDraftError("草案规则层收到不一致的旅行需求，未生成行程。") from error

    # 需求不完整时在模型调用之前结束，避免生成看似可用的半成品。
    if not clarification_plan.is_complete:
        return clarification_plan

    runnable = generator or create_structured_itinerary_generator()
    try:
        raw_suggestions = runnable.invoke({"request_context": _build_request_context(request)})
        suggestions = ItinerarySuggestions.model_validate(raw_suggestions)
        _validate_suggestions(suggestions, request.days)
        return _assemble_draft(request, suggestions)
    except ValidationError as error:
        raise ItineraryStructuredOutputError(
            "模型返回的每日建议未通过 Pydantic 校验，未生成行程草案。"
        ) from error
    except ItineraryStructuredOutputError:
        raise
    except ItineraryDraftError:
        raise
    except ItineraryModelConfigurationError:
        raise
    except Exception as error:
        raise ItineraryModelInvocationError(
            "模型调用失败，未生成行程草案。请检查模型服务和网络后重试。"
        ) from error


def _validate_request_for_draft(request: TravelRequest) -> None:
    """拒绝绕过 Pydantic 校验或篡改缺失字段状态的输入。"""
    if not isinstance(request, TravelRequest):
        raise ItineraryDraftError("草案规则层只接受已通过 Pydantic 校验的 TravelRequest。")
    try:
        expected_fields = calculate_missing_fields(request)
        if request.missing_fields != expected_fields:
            raise ItineraryDraftError("草案规则层输入不一致：missing_fields 与 TravelRequest 不匹配。")
        validated_request = TravelRequest.model_validate(request.model_dump())
        if validated_request.missing_fields != request.missing_fields:
            raise ItineraryDraftError("草案规则层输入不一致：missing_fields 与 TravelRequest 不匹配。")
    except ValidationError as error:
        raise ItineraryDraftError("草案规则层收到未通过 Pydantic 校验的 TravelRequest。") from error


def _build_request_context(request: TravelRequest) -> dict[str, object]:
    """只传递已知业务上下文，不让模型决定工作流字段。"""
    return {
        "destination": request.destination,
        "days": request.days,
        "traveler_count": request.traveler_count,
        "budget": request.budget,
        "preferences": request.preferences,
        "constraints": request.constraints,
    }


def _validate_suggestions(suggestions: ItinerarySuggestions, days: int | None) -> None:
    """验证模型仅提供恰好所需天数且没有确认承诺的建议。"""
    if days is None or len(suggestions.daily_suggestions) != days:
        raise ItineraryStructuredOutputError("模型返回的每日建议数量与旅行天数不一致，未生成行程草案。")

    for suggestion in suggestions.daily_suggestions:
        texts = [suggestion.theme]
        for activity in suggestion.activities:
            texts.extend([activity.title, activity.description])
        if any(term in text.lower() for text in texts for term in FORBIDDEN_COMMITMENT_TERMS):
            raise ItineraryStructuredOutputError(
                "模型建议含有未经支持的确认或预订承诺，未生成行程草案。"
            )
        if any(
            not any(term in activity.description for term in SUGGESTION_TERMS)
            for activity in suggestion.activities
        ):
            raise ItineraryStructuredOutputError(
                "模型活动说明未保留建议语义，未生成行程草案。"
            )


def _assemble_draft(request: TravelRequest, suggestions: ItinerarySuggestions) -> ItineraryDraft:
    """以程序日期骨架组合已经验证的建议，不改写用户需求。"""
    if (
        request.destination is None
        or request.start_date is None
        or request.end_date is None
        or request.days is None
        or request.traveler_count is None
        or request.budget is None
    ):
        raise ItineraryDraftError("完整旅行需求缺少必要字段，未生成行程草案。")

    daily_items = [
        DailyItineraryItem(
            day_number=index,
            date=request.start_date + timedelta(days=index - 1),
            theme=suggestion.theme,
            activities=suggestion.activities,
        )
        for index, suggestion in enumerate(suggestions.daily_suggestions, start=1)
    ]
    return ItineraryDraft(
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        days=request.days,
        traveler_count=request.traveler_count,
        budget=request.budget,
        preferences=request.preferences,
        constraints=request.constraints,
        daily_items=daily_items,
        notes=[
            "本行程为可编辑草案；所有活动仅为建议。",
            "景点开放、价格、路线、天气、库存和预订状态均未核实，需在后续阶段确认。",
        ],
    )
