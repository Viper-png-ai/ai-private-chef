from __future__ import annotations
from pathlib import Path
import sqlite3
from collections.abc import Iterator
from typing import Any

from langchain.agents import create_agent
from langchain.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver

from hello_world.app.core.config import settings

import json
from dataclasses import dataclass
from typing import TypedDict

from langchain.tools import ToolRuntime, tool
from langgraph.store.sqlite import SqliteStore

from hello_world.app.core.safety import find_allergen_terms

from datetime import date
from hello_world.app.services.pantry import (
    create_pantry_item,
    delete_pantry_item,
    list_pantry_items,
    update_pantry_item,
)

#1.创建模型
model = ChatOpenAI(
    model_name="qwen3.8-flash",
    base_url=settings.dashscope_base_url,
    api_key=settings.dashscope_api_key
    
)

#2.工具
web_search = TavilySearch(
    max_results=5,
    topic="general"
)

#3.1 创建checkpointer
connection = sqlite3.connect(
    settings.sqlite_path,
    check_same_thread=False,
)
checkpointer = SqliteSaver(connection)

checkpointer.setup()

#3.2 创建store
store_connection = sqlite3.connect(
    settings.sqlite_path,
    check_same_thread=False,
    isolation_level=None,
)

store = SqliteStore(store_connection)
store.setup()

@dataclass
class UserContext:
    user_id: str


class UserPreferences(TypedDict, total=False):
    name: str
    allergies: list[str]
    dislikes: list[str]
    favorite_foods: list[str]
    taste: str
    cooking_skill: str
    household_size: int
    kitchen_tools: list[str]
    nutrition_goal: str
    extra_notes: list[str]

@tool
def read_user_profile(runtime: ToolRuntime[UserContext]) -> str:
    """读取当前用户的长期饮食偏好、忌口和做饭习惯。"""
    if runtime.store is None:
        return "{}"

    item = runtime.store.get(
        ("users",),
        runtime.context.user_id,
    )

    if item is None:
        return "{}"

    return json.dumps(
        item.value,
        ensure_ascii=False,
    )
@tool
def save_user_preferences(preferences: UserPreferences,runtime: ToolRuntime[UserContext]) -> str:
    """保存用户明确说出的长期饮食偏好、过敏信息、忌口和习惯。"""
    if runtime.store is None:
        return "长期记忆存储不可用。"

    user_id = runtime.context.user_id
    item = runtime.store.get(("users",), user_id)
    current = dict(item.value) if item else {}

    for key, value in preferences.items():
        if value is not None:
            current[key] = value

    runtime.store.put(
        ("users",),
        user_id,
        current,
    )

    return "用户长期饮食偏好已保存。"

@tool
def check_recipe_safety(
    recipe_text:str,
    runtime:ToolRuntime[UserContext],
)->str:
    """检查候选菜谱是否包含用户长期记录的过敏原。"""
    if runtime.store is None:
        return json.dumps(
            {
                "safe": False,
                "message": "安全存储不可用，无法完成过敏原检查。",
            },
            ensure_ascii=False,
        )

    item = runtime.store.get(
        ("users",),
        runtime.context.user_id,
    )

    profile = dict(item.value) if item else {}
    allergies = profile.get("allergies") or []

    matched_allergens = find_allergen_terms(
        recipe_text,
        allergies,
    )

    return json.dumps(
        {
            "safe": not matched_allergens,
            "allergies": allergies,
            "matched_allergens": matched_allergens,
            "message": (
                "菜谱未发现用户记录的过敏原。"
                if not matched_allergens
                else "菜谱可能包含用户过敏原，必须停止推荐。"
            ),
        },
        ensure_ascii=False,
    )

def _pantry_with_expiry(
    user_id: str,
) -> list[dict[str, object]]:
    items = list_pantry_items(user_id)
    today = date.today()

    for item in items:
        expires_at = item.get("expires_at")

        if not expires_at:
            item["days_until_expiry"] = None
            item["freshness"] = "unknown"
            continue

        try:
            expiry_date = date.fromisoformat(
                str(expires_at)[:10]
            )
        except ValueError:
            item["days_until_expiry"] = None
            item["freshness"] = "unknown"
            continue

        days = (expiry_date - today).days
        item["days_until_expiry"] = days

        if days < 0:
            item["freshness"] = "expired"
        elif days <= 3:
            item["freshness"] = "expiring_soon"
        else:
            item["freshness"] = "fresh"

    return items


@tool
def read_pantry(
    runtime: ToolRuntime,
) -> str:
    """读取当前用户的食材库存、数量和过期时间。"""
    items = _pantry_with_expiry(
        runtime.context.user_id,
    )

    return json.dumps(
        items,
        ensure_ascii=False,
    )

@tool
def add_pantry_item_tool(
    name: str,
    quantity: float,
    unit: str,
    expires_at: str | None,
    runtime: ToolRuntime,
) -> str:
    """用户明确要求把一种食材加入库存时使用。"""
    if quantity <= 0:
        return json.dumps(
            {
                "success": False,
                "message": "数量必须大于 0。",
            },
            ensure_ascii=False,
        )

    item = create_pantry_item(
        user_id=runtime.context.user_id,
        name=name.strip(),
        quantity=quantity,
        unit=unit.strip(),
        expires_at=expires_at,
    )

    return json.dumps(
        {
            "success": True,
            "message": f"已加入库存：{name}",
            "item": item,
        },
        ensure_ascii=False,
    )


@tool
def consume_pantry_item_tool(
    name: str,
    amount: float,
    runtime: ToolRuntime,
) -> str:
    """用户明确表示已经使用、吃掉或消耗某种食材时使用。"""
    if amount <= 0:
        return json.dumps(
            {
                "success": False,
                "message": "消耗数量必须大于 0。",
            },
            ensure_ascii=False,
        )

    user_id = runtime.context.user_id
    items = list_pantry_items(user_id)

    matches = [
        item
        for item in items
        if str(item["name"]).strip().lower()
        == name.strip().lower()
    ]

    if not matches:
        return json.dumps(
            {
                "success": False,
                "message": f"库存中没有找到“{name}”。",
            },
            ensure_ascii=False,
        )

    if len(matches) > 1:
        return json.dumps(
            {
                "success": False,
                "message": (
                    f"库存中存在多个“{name}”，"
                    "请让用户说明具体是哪一项。"
                ),
            },
            ensure_ascii=False,
        )

    item = matches[0]
    item_id = str(item["id"])
    old_quantity = float(item["quantity"])
    remaining = old_quantity - amount

    if remaining <= 0:
        delete_pantry_item(user_id, item_id)
        message = f"已用完并移除库存中的“{name}”。"
    else:
        update_pantry_item(
            user_id=user_id,
            item_id=item_id,
            changes={"quantity": remaining},
        )
        message = (
            f"已消耗 {amount} {item['unit']}“{name}”，"
            f"剩余 {remaining} {item['unit']}。"
        )

    return json.dumps(
        {
            "success": True,
            "message": message,
            "old_quantity": old_quantity,
            "remaining": max(remaining, 0),
        },
        ensure_ascii=False,
    )

#4.创建智能体
system_prompt = """
你是“AI私厨”，用简体中文提供食材识别、营养搭配和家常菜建议。

规则：
1. 用户询问食材、菜谱或饮食建议时，先读取其长期偏好，包括过敏、忌口、人数、厨艺水平和营养目标。
2. 只有用户明确说出长期有效的信息时才保存长期记忆；不要保存一次性需求，也不要猜测或保存用户未提供的姓名和偏好。
3. 用户询问现有食材或冰箱库存时，必须先读取库存。优先使用临期食材，禁止使用已过期食材；没有过期日期的食材不要判断新鲜度。
4. 只有用户明确要求“加入库存”“记录到库存”“已经使用”“吃掉”或“消耗了”时，才能修改库存。缺少数量或单位时先询问，不得因为推荐菜谱而自动修改库存。
5. 用户提供照片或清单时，识别食材并判断可用性。不确定的食材要标注；变质或无法确认安全的食材要提醒不要使用。
6. 只有需要菜谱、做法或外部信息时才搜索，同一轮最多搜索一次。不要编造菜谱、营养数据或图片链接；图片只能使用可访问的图片直链。
7. 输出任何含食材的菜谱前，必须对每个具体菜谱单独检查过敏原。新增菜谱、替换菜谱、替换酱料或替换食材都要重新检查，不能复用上一道菜的安全结论。
8. 过敏信息和明确忌口优先级最高。检查不安全时必须放弃方案并说明冲突；无法确认成分是否安全时，要说明不确定性并请用户确认。
9. 菜谱评分共 100 分：营养价值 0-50 分，制作难度 0-50 分，越简单分越高。没有精确营养数据时使用估算。
10. 用户提供食材时，输出当前可用食材、不超过 3 个菜谱（菜名、评分、用时、食材、推荐理由、步骤、替代方案）、推荐结论和风险提示。缺少食材要明确说明。
11. 用户只询问买菜、保存、饮食搭配或烹饪技巧时，直接给出简洁建议，不必套用完整菜谱模板。
12. 所有输出必须使用简体中文，禁止英文句子或中英文混写。
13. 工具调用前不要输出过渡语，工具调用完成后再输出最终结果。不要提及内部工具名称，也不要描述“正在读取”“正在检查”等过程。
14. 只有实际检查过某个具体菜谱后，才能说它已通过安全检查；未检查的菜谱必须标注“未完成过敏原检查”。
15. 过敏风险只做必要提示。出现口唇发麻、皮疹、呼吸不畅等严重症状时，提醒立即就医，不展开诊断或治疗方案。
"""


agent = create_agent(
    model=model,
    tools=[
        web_search,
        read_user_profile,
        save_user_preferences,
        check_recipe_safety,
        read_pantry,
        add_pantry_item_tool,
        consume_pantry_item_tool,
    ],
    system_prompt=system_prompt,
    checkpointer=checkpointer,
    store=store,
    context_schema=UserContext,
)

def _config(session_id:str)->dict[str,dict[str,str]]:
    return {
        "configurable":{
            "thread_id":session_id,
        }
    }

def _content_to_text(content:Any)->str:
    if isinstance(content,str):
        return content

    if not isinstance(content,list):
        return ""

    parts:list[str]=[]

    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            text = block.get("text")
            if block.get("type") == "text" and isinstance(text, str):
                parts.append(text)

    return "".join(parts)

def build_user_message(
        message:str,
        image_url:str | None = None,
)->HumanMessage:
    if not image_url:
        return HumanMessage(content=message)

    return HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                },
            },
            {
                "type": "text",
                "text": message,
            },
        ]
    )

def stream_agent_reply(
    message: str,
    user_id: str,
    session_id: str,
    image_url: str | None = None,
) -> Iterator[str]:
    user_message = build_user_message(message, image_url)

    for chunk, _metadata in agent.stream(
        {"messages": [user_message]},
        config=_config(session_id),
        context=UserContext(user_id=user_id),
        stream_mode="messages",
    ):
        if not isinstance(chunk, AIMessageChunk):
            continue

        if getattr(chunk, "tool_call_chunks", None):
            continue

        text = _content_to_text(chunk.content)

        if text:
            yield text

def get_history(session_id:str)->list[dict[str,object]]:
    try:
        snapshot = agent.get_state(_config(session_id))
    except Exception:
        return []

    if not snapshot or not snapshot.values:
        return []

    messages = snapshot.values.get("messages") or []
    result:list[dict[str,str]]=[]

    for message in messages:
        if isinstance(message,HumanMessage):
            role = "user"
        elif isinstance(message,AIMessage):
            role = "assistant"
        else:
            continue

        content = _content_to_text(message.content)

        if content:
            result.append(
                {
                    "role":role,
                    "content":content,
                }
            )
    return result

def list_sessions(
    user_id: str,
    limit: int = 50,
) -> list[dict[str, str]]:
    prefix = f"{user_id}:"

    rows = connection.execute(
        """
        SELECT thread_id, MAX(checkpoint_id) AS latest
        FROM checkpoints
        WHERE thread_id LIKE ?
        GROUP BY thread_id
        ORDER BY latest DESC
        LIMIT ?
        """,
        (f"{prefix}%", limit),
    ).fetchall()

    sessions: list[dict[str, str]] = []

    for row in rows:
        scoped_thread_id = row[0]
        client_session_id = scoped_thread_id.removeprefix(prefix)
        history = get_history(scoped_thread_id)

        title = next(
            (
                item["content"]
                for item in history
                if item["role"] == "user"
            ),
            client_session_id,
        )

        sessions.append(
            {
                "session_id": client_session_id,
                "title": title[:30],
            }
        )

    return sessions

def clear_history(session_id:str)->None:
    checkpointer.delete_thread(session_id)

