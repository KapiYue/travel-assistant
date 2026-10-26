"""Structured extraction of a travel request from natural-language input."""

from __future__ import annotations

import os
from typing import Any, Protocol

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from backend.travel_assistant.models import TravelRequest, TravelRequestExtraction

EXTRACTION_SYSTEM_PROMPT = """你是旅行需求提取器，只返回符合结构化 schema 的数据。

只提取用户明确表达的信息，或可以从明确的出发日期和天数唯一计算的信息。
不得根据常识、目的地、同行关系或偏好猜测日期、人数、预算、景点或其他字段。
日期只有在能确定年份时才填写，使用 YYYY-MM-DD；无法确定时填 null。
“带父母”“和家人同行”等关系不等于明确人数，除非用户给出总人数。
保留预算的原始金额、范围或档位表述，不自行换算。
preferences 记录想获得的体验；constraints 记录必须遵守的限制。没有对应信息时使用空数组。
不要计算 missing_fields；该字段完全由程序处理。"""


class EmptyTravelRequestError(ValueError):
    """Raised when there is no user description to extract."""


class ModelConfigurationError(RuntimeError):
    """Raised when local model settings required for extraction are absent."""


class ModelInvocationError(RuntimeError):
    """Raised when a configured model cannot complete the extraction call."""


class StructuredOutputValidationError(RuntimeError):
    """Raised when the model response does not satisfy the extraction schema."""


class StructuredExtractor(Protocol):
    """The small interface needed from the LangChain extraction runnable."""

    def invoke(self, input_value: dict[str, str]) -> Any:
        """Return a structured extraction for the prompt input."""


def create_structured_extractor() -> StructuredExtractor:
    """Build the configured LangChain prompt and Structured Output runnable."""
    load_dotenv()
    api_key = os.getenv("DATA_API_KEY") or os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("DATA_MODEL") or os.getenv("OPENAI_MODEL")
    base_url = os.getenv("DATA_BASE_URL") or os.getenv("OPENAI_BASE_URL") or None

    if not api_key or not model_name:
        raise ModelConfigurationError(
            "缺少模型配置。请复制 .env.example 为 .env，并填写 DATA_API_KEY 和 DATA_MODEL。"
        )

    prompt = ChatPromptTemplate.from_messages(
        [("system", EXTRACTION_SYSTEM_PROMPT), ("human", "{user_input}")]
    )
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )
    return prompt | llm.with_structured_output(TravelRequestExtraction)


def extract_travel_request(
    user_input: str, extractor: StructuredExtractor | None = None
) -> TravelRequest:
    """Extract and validate one request without fabricating missing information."""
    normalized_input = user_input.strip()
    if not normalized_input:
        raise EmptyTravelRequestError("请输入旅行需求，例如：两个人 2026 年 11 月去杭州玩 3 天。")

    runnable = extractor or create_structured_extractor()
    try:
        raw_extraction = runnable.invoke({"user_input": normalized_input})
        extraction = TravelRequestExtraction.model_validate(raw_extraction)
        return TravelRequest.model_validate(extraction.model_dump())
    except ValidationError as error:
        raise StructuredOutputValidationError(
            "模型返回的结构化数据未通过 Pydantic 校验，未生成旅行需求。"
        ) from error
    except (EmptyTravelRequestError, ModelConfigurationError, StructuredOutputValidationError):
        raise
    except Exception as error:
        raise ModelInvocationError(
            "模型调用失败，未生成旅行需求。请检查模型服务和网络后重试。"
        ) from error
