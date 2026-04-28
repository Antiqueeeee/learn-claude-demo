from __future__ import annotations

from typing import Any

from tool_runtime.base import BaseTool

RATES = {
    ("USD", "JPY"): 150.0,
    ("JPY", "KRW"): 9.0,
    ("KRW", "VND"): 19.0,
    ("VND", "IDR"): 0.65,
}

COUNTRY_BY_CURRENCY = {
    "USD": "美国",
    "JPY": "日本",
    "KRW": "韩国",
    "VND": "越南",
    "IDR": "印度尼西亚",
}


class FxConvertTool(BaseTool):
    name = "fx_convert"
    description = (
        "Convert currency using ONLY adjacent pairs on a fixed path: "
        "USD->JPY->KRW->VND->IDR. "
        "Direct non-adjacent conversions are not supported."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Amount in from_currency.",
            },
            "from_currency": {
                "type": "string",
                "enum": ["USD", "JPY", "KRW", "VND", "IDR"],
                "description": "Source currency code.",
            },
            "to_currency": {
                "type": "string",
                "enum": ["USD", "JPY", "KRW", "VND", "IDR"],
                "description": (
                    "Target currency code (must be adjacent to from_currency on the path)."
                ),
            },
        },
        "required": ["amount", "from_currency", "to_currency"],
        "additionalProperties": False,
    }

    def run(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        source_currency = from_currency.upper()
        target_currency = to_currency.upper()
        pair = (source_currency, target_currency)

        if pair not in RATES:
            allowed_pairs = ", ".join(
                f"{source}->{target}"
                for source, target in RATES
            )
            raise ValueError(
                f"Unsupported direct conversion: {source_currency}->{target_currency}. "
                f"Only adjacent pairs are allowed: {allowed_pairs}"
            )

        rate = RATES[pair]
        return {
            "from_currency": source_currency,
            "from_country": COUNTRY_BY_CURRENCY.get(source_currency, source_currency),
            "to_currency": target_currency,
            "to_country": COUNTRY_BY_CURRENCY.get(target_currency, target_currency),
            "amount": amount,
            "rate": rate,
            "result": amount * rate,
        }


TOOL = FxConvertTool()
