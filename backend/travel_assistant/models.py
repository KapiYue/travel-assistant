"""Validated data models for the travel-assistant workflow."""

from __future__ import annotations

import datetime
import re
from datetime import date, timedelta
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

REQUIRED_REQUEST_FIELDS = (
    "destination",
    "start_date",
    "days",
    "traveler_count",
    "budget",
)

CLARIFICATION_QUESTIONS = {
    "destination": (
        "这次旅行想去哪个目的地？",
        "需要确认本次旅行的目的地。",
    ),
    "start_date": (
        "请问计划哪一年哪月哪日出发？请包含年份。",
        "需要确认包含年份的出发日期，避免跨年歧义。",
    ),
    "days": (
        "请问这次旅行计划玩几天？请提供大于 0 的整数。",
        "需要确认旅行天数，且天数必须为大于 0 的整数。",
    ),
    "traveler_count": (
        "请问这次一共几个人出行？",
        "需要确认总出行人数；同行关系不能代表人数。",
    ),
    "budget": (
        "请问这次旅行的预算大约是多少？也可以告诉我预算范围或档位。",
        "需要确认预算金额、范围或档位，并保留原本表述。",
    ),
}

FORBIDDEN_ACTIVITY_TERMS = (
    "已确认",
    "已预订",
    "已订",
    "confirmed",
    "booked",
    "票价",
    "门票",
    "营业时间",
    "开放时间",
    "库存",
    "预订链接",
    "http://",
    "https://",
)
SUGGESTION_TERMS = ("建议", "可考虑", "可安排")


class ClarificationQuestion(BaseModel):
    """One program-generated question for a required but unknown field."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str = Field(description="需要用户补充的旅行需求字段。")
    prompt: str = Field(description="面向用户的清晰、礼貌中文追问。")
    reason: str = Field(description="说明为何需要补充该字段的简短原因。")


class ClarificationPlan(BaseModel):
    """A deterministic, non-speculative plan for asking missing travel details.

    Only ``missing_fields`` is accepted as input. The remaining fields are
    derived by this model so callers cannot assert a false completion state or
    attach arbitrary questions.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    missing_fields: list[str] = Field(
        default_factory=list,
        description="已校验旅行需求中仍缺失的必填字段，按固定顺序展示。",
    )
    questions: list[ClarificationQuestion] = Field(
        default_factory=list,
        description="由缺失字段确定性生成的中文追问。",
    )
    is_complete: bool = Field(
        default=False,
        description="当且仅当没有缺失必填字段时为 true。",
    )
    message: str = Field(
        default="",
        description="说明是否仍需补充信息的程序生成提示。",
    )

    _derived_fields: ClassVar[frozenset[str]] = frozenset(
        {"questions", "is_complete", "message"}
    )

    @model_validator(mode="before")
    @classmethod
    def reject_forged_derived_values(cls, value: object) -> object:
        """Keep status and wording under program control rather than caller input."""
        if isinstance(value, dict):
            supplied = cls._derived_fields.intersection(value)
            if supplied:
                names = "、".join(sorted(supplied))
                raise ValueError(f"{names} 必须由追问规则层计算，不能由调用方提供")
        return value

    @field_validator("missing_fields")
    @classmethod
    def validate_missing_fields(cls, values: list[str]) -> list[str]:
        """Reject unknown or repeated fields and normalize to workflow order."""
        unknown = [value for value in values if value not in REQUIRED_REQUEST_FIELDS]
        if unknown:
            raise ValueError("追问规则层收到未知缺失字段")
        if len(values) != len(set(values)):
            raise ValueError("追问规则层收到重复缺失字段")
        return [field_name for field_name in REQUIRED_REQUEST_FIELDS if field_name in values]

    @model_validator(mode="after")
    def derive_plan(self) -> "ClarificationPlan":
        """Derive all display fields from the validated missing-field list."""
        object.__setattr__(
            self,
            "questions",
            [
                ClarificationQuestion(
                    field=field_name,
                    prompt=CLARIFICATION_QUESTIONS[field_name][0],
                    reason=CLARIFICATION_QUESTIONS[field_name][1],
                )
                for field_name in self.missing_fields
            ],
        )
        object.__setattr__(self, "is_complete", not self.missing_fields)
        object.__setattr__(
            self,
            "message",
            (
                "信息已齐全，可以进入后续阶段。"
                if self.is_complete
                else "仍需补充以下旅行信息，补充后才能进入后续阶段。"
            ),
        )
        return self


class TravelRequestFields(BaseModel):
    """Business fields that a model may extract from a travel description."""

    model_config = ConfigDict(extra="forbid")

    destination: str | None = Field(
        default=None,
        description="用户明确表达的目的地；未表达时为 null。",
    )
    start_date: date | None = Field(
        default=None,
        description="可确定且包含年份的出发日期，格式为 YYYY-MM-DD；未知时为 null。",
    )
    end_date: date | None = Field(
        default=None,
        description="用户明确表达，或可由确定的出发日期和天数唯一算出的结束日期；未知时为 null。",
    )
    days: StrictInt | None = Field(
        default=None,
        gt=0,
        description="旅行天数，必须是大于 0 的整数；未知时为 null。",
    )
    traveler_count: StrictInt | None = Field(
        default=None,
        gt=0,
        description="明确说明的出行人数，必须是大于 0 的整数；未知时为 null。",
    )
    budget: str | None = Field(
        default=None,
        description="用户原样表达的预算金额、范围或档位；未知时为 null。",
    )
    preferences: list[str] = Field(
        default_factory=list,
        description="用户希望获得的体验，例如自然风景、美食或慢节奏。",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="必须遵守的限制，例如老人同行、不能吃辣或不想安排太赶。",
    )

# Pydantic 会在校验可选文本字段时自动调用 normalize_optional_text。
# 比如request = TravelRequest(
#     preferences=[" 自然风景 ", "自然风景", ""]
# )
# 会得到[" 自然风景 "]

    @field_validator("destination", "budget", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Strip optional text while treating a blank model value as unknown."""
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("preferences", "constraints")
    @classmethod
    def normalize_text_list(cls, values: list[str]) -> list[str]:
        """Remove blank repeated labels while preserving the user's stated order."""
        normalized_values: list[str] = []
        for value in values:
            normalized = value.strip()
            if normalized and normalized not in normalized_values:
                normalized_values.append(normalized)
        return normalized_values

# field_validator只校验一个字段本身，model_validator校验多个字段之间的关系
    @model_validator(mode="after")
    def validate_date_order(self) -> "TravelRequestFields":
        """Reject an end date that precedes the stated start date."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("结束日期不能早于出发日期")
        return self


# 给模型使用的结构化输出格式
class TravelRequestExtraction(TravelRequestFields):
    """The schema supplied to the model for business-field extraction only."""

# 给业务用的，最终业务对象
class TravelRequest(TravelRequestFields):
    """The validated request consumed by the next workflow stage.

    ``missing_fields`` is deliberately absent from ``TravelRequestExtraction``.
    It is calculated below by ordinary Python code after extraction, rather than
    relying on the model to decide whether planning information is sufficient.
    """

    missing_fields: list[str] = Field(
        default_factory=list,
        description="由程序按照当前规划前必填规则计算出的缺失字段。",
    )

    @model_validator(mode="after")
    def complete_derived_fields(self) -> "TravelRequest":
        """Derive a deterministic end date and recalculate required omissions."""
        if self.end_date is None and self.start_date is not None and self.days is not None:
            self.end_date = self.start_date + timedelta(days=self.days - 1)

        self.missing_fields = calculate_missing_fields(self)
        return self


class ActivitySuggestion(BaseModel):
    """一项可编辑且尚未核实的活动建议。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = Field(min_length=1, description="活动建议的简短标题，不代表已确认安排。")
    description: str = Field(
        min_length=1,
        description="活动建议的说明，必须保留建议语气且不得承诺实时事实。",
    )
    verification_status: Literal["unverified"] = Field(
        default="unverified",
        description="动态信息尚未核实，不能表示已确认、已预订或可用。",
    )

    @field_validator("title", "description")
    @classmethod
    def reject_unverified_dynamic_claims(cls, value: str) -> str:
        """拒绝把未接入工具的动态事实或预订承诺写进活动文本。"""
        lowered_value = value.lower()
        if any(term in lowered_value for term in FORBIDDEN_ACTIVITY_TERMS):
            raise ValueError("活动建议不能包含实时事实、价格、预订链接或确认承诺")
        if re.search(r"\d+\s*(元|人民币|rmb|cny)", lowered_value):
            raise ValueError("活动建议不能包含未经核实的精确价格")
        return value

    @field_validator("description")
    @classmethod
    def require_suggestion_wording(cls, value: str) -> str:
        """确保活动文本明确是建议，而不是既定安排。"""
        if not any(term in value for term in SUGGESTION_TERMS):
            raise ValueError("活动说明必须保留建议语义")
        return value


class DailyItineraryItem(BaseModel):
    """由程序确定日期与编号的一天草案。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    day_number: StrictInt = Field(gt=0, description="由程序从 1 开始连续计算的旅行日编号。")
    date: datetime.date = Field(description="由程序根据出发日期连续计算的当日日期。")
    theme: str = Field(min_length=1, description="当天的可编辑建议主题。")
    activities: list[ActivitySuggestion] = Field(
        min_length=1,
        description="当天的可编辑活动建议，均为未验证状态。",
    )


class ItineraryDraft(BaseModel):
    """完整旅行需求对应的结构化可编辑行程草案。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["draft"] = Field(
        default="draft",
        description="固定为草案，不能表示任何已确认行程或预订结果。",
    )
    destination: str = Field(min_length=1, description="直接沿用完整旅行需求中的目的地。")
    start_date: date = Field(description="直接沿用完整旅行需求中的出发日期。")
    end_date: date = Field(description="直接沿用完整旅行需求中的结束日期。")
    days: StrictInt = Field(gt=0, description="直接沿用完整旅行需求中的旅行天数。")
    traveler_count: StrictInt = Field(gt=0, description="直接沿用完整旅行需求中的出行人数。")
    budget: str = Field(min_length=1, description="直接沿用用户原样表达的预算。")
    preferences: list[str] = Field(default_factory=list, description="直接沿用用户已表达的偏好。")
    constraints: list[str] = Field(default_factory=list, description="直接沿用用户已表达的限制。")
    daily_items: list[DailyItineraryItem] = Field(
        min_length=1,
        description="每天一项的连续日期草案，由程序校验数量、编号和日期。",
    )
    notes: list[str] = Field(
        min_length=1,
        description="程序附加的未验证事实提示，不应被当作实时结论。",
    )

    @model_validator(mode="after")
    def validate_daily_skeleton(self) -> "ItineraryDraft":
        """确保每日草案与已经校验的日期和天数完全一致。"""
        if self.end_date != self.start_date + timedelta(days=self.days - 1):
            raise ValueError("草案结束日期与出发日期、天数不一致")
        if len(self.daily_items) != self.days:
            raise ValueError("每日草案数量必须与旅行天数一致")

        for index, item in enumerate(self.daily_items, start=1):
            expected_date = self.start_date + timedelta(days=index - 1)
            if item.day_number != index or item.date != expected_date:
                raise ValueError("每日草案编号或日期与程序计算结果不一致")
        return self


def calculate_missing_fields(request: TravelRequestFields) -> list[str]:
    """Return planning fields that are still unknown, in stable display order."""
    return [
        field_name
        for field_name in REQUIRED_REQUEST_FIELDS
        if getattr(request, field_name) is None
    ]
