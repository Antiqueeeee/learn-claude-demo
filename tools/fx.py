# tools/fx.py
from __future__ import annotations

# 只允许相邻兑换（示例汇率是虚构的，用来测试多步 tool call）
RATES = {
    ("USD", "JPY"): 150.0,      # 美国->日本
    ("JPY", "KRW"): 9.0,        # 日本->韩国
    ("KRW", "VND"): 19.0,       # 韩国->越南
    ("VND", "IDR"): 0.65,       # 越南->印度尼西亚
}

COUNTRY_BY_CCY = {
    "USD": "美国",
    "JPY": "日本",
    "KRW": "韩国",
    "VND": "越南",
    "IDR": "印度尼西亚",
}

def fx_convert(amount: float, from_currency: str, to_currency: str):
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    pair = (from_currency, to_currency)
    if pair not in RATES:
        allowed = ", ".join([f"{a}->{b}" for a, b in RATES.keys()])
        raise ValueError(
            f"Unsupported direct conversion: {from_currency}->{to_currency}. "
            f"Only adjacent pairs are allowed: {allowed}"
        )

    rate = RATES[pair]
    result = amount * rate
    return {
        "from_currency": from_currency,
        "from_country": COUNTRY_BY_CCY.get(from_currency, from_currency),
        "to_currency": to_currency,
        "to_country": COUNTRY_BY_CCY.get(to_currency, to_currency),
        "amount": amount,
        "rate": rate,
        "result": result,
    }
