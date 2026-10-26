"""Validated data models for the travel-assistant workflow."""

from __future__ import annotations

from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

REQUIRED_REQUEST_FIELDS = (
    "destination",
    "start_date",
    "days",
    "traveler_count",
    "budget",
)


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

# normalize_optional_text函数会被 Pydantic 自动调用。
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


def calculate_missing_fields(request: TravelRequestFields) -> list[str]:
    """Return planning fields that are still unknown, in stable display order."""
    return [
        field_name
        for field_name in REQUIRED_REQUEST_FIELDS
        if getattr(request, field_name) is None
    ]
