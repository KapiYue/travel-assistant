"""Deterministic clarification planning for a validated travel request."""

from __future__ import annotations

from pydantic import ValidationError

from backend.travel_assistant.models import (
    ClarificationPlan,
    TravelRequest,
    calculate_missing_fields,
)


class ClarificationPlanError(ValueError):
    """Raised when a request is not a consistent, validated workflow input."""


def create_clarification_plan(request: TravelRequest) -> ClarificationPlan:
    """Create a complete or missing-information plan without calling a model.

    The function accepts only a ``TravelRequest`` and checks that its derived
    missing-field state still matches its validated business values. This avoids
    returning a partial or falsely complete plan for tampered workflow input.
    """
    # request 这个对象，是否由 TravelRequest 这个类创建，或者是否属于它的子类？
    if not isinstance(request, TravelRequest):
        raise ClarificationPlanError("追问规则层只接受已通过 Pydantic 校验的 TravelRequest。")

# actual_fields = request.missing_fields,确认对象内部的缺失字段状态没有被篡改。
    try:
        expected_fields = calculate_missing_fields(request)
        actual_fields = request.missing_fields
    except (AttributeError, TypeError) as error:
        raise ClarificationPlanError("追问规则层收到不完整的 TravelRequest。") from error

    if actual_fields != expected_fields:
        raise ClarificationPlanError("追问规则层输入不一致：missing_fields 与 TravelRequest 不匹配。")

    try:
        # Revalidate to reject instances that were constructed while bypassing
        # Pydantic validation, such as TravelRequest.model_construct(days=0).
        validated_request = TravelRequest.model_validate(request.model_dump())
        if validated_request.missing_fields != actual_fields:
            raise ClarificationPlanError(
                "追问规则层输入不一致：missing_fields 与 TravelRequest 不匹配。"
            )
        return ClarificationPlan(missing_fields=actual_fields)
    except ValidationError as error:
        raise ClarificationPlanError("追问规则层收到未通过 Pydantic 校验的 TravelRequest。") from error
    except ClarificationPlanError:
        raise
    except ValueError as error:
        raise ClarificationPlanError("追问规则层生成计划失败，未返回部分问题。") from error
