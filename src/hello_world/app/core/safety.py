from __future__ import annotations

ALLERGEN_ALIASES: dict[str, list[str]] = {
    "花生": [
        "花生",
        "花生油",
        "花生酱",
        "花生碎",
        "花生粉",
        "土榨花生油",
    ],
    "海鲜": [
        "海鲜",
        "虾",
        "蟹",
        "贝",
        "鱼露",
        "蚝油",
        "海参",
        "鱿鱼",
    ],
    "鸡蛋": [
        "鸡蛋",
        "蛋清",
        "蛋黄",
        "蛋液",
    ],
    "牛奶": [
        "牛奶",
        "奶油",
        "黄油",
        "奶粉",
        "芝士",
        "奶酪",
    ],
    "坚果": [
        "坚果",
        "核桃",
        "腰果",
        "杏仁",
        "开心果",
        "榛子",
        "松子",
    ],
    "大豆": [
        "大豆",
        "黄豆",
        "豆腐",
        "豆浆",
        "豆豉",
        "酱油",
    ],
    "小麦": [
        "小麦",
        "面粉",
        "面包",
        "面条",
        "饼干",
    ],
}

def find_allergen_terms(
    text: str,
    allergies: list[str],
) -> list[str]:
    normalized_text = text.replace(" ", "").lower()
    matches: set[str] = set()

    for allergy in allergies:
        aliases = ALLERGEN_ALIASES.get(
            allergy,
            [allergy],
        )

        for alias in aliases:
            if alias and alias.lower() in normalized_text:
                matches.add(alias)

    return sorted(matches)