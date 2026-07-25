from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal, Annotated
from langgraph.graph import add_messages


class Router(BaseModel):
    """分析未读邮件并根据内容路由。"""

    reasoning: str = Field(description="得出该分类的逐步推理过程（用中文）。")
    # 枚举值保留英文：function calling 的 schema 约束 + 代码分支判断依赖这三个值
    classification: Literal["ignore", "respond", "notify"] = Field(
        description="邮件分类：'ignore'=无关邮件直接忽略；"
        "'notify'=重要信息但无需回复；'respond'=需要回复的邮件",
    )

class State(TypedDict):
    email_input: str
    messages: Annotated[list, add_messages]
