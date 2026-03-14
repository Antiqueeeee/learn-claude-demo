
from modes.the_agent_loop import naive_run

messages = [
  {"role":"user","content":"我有10美元（美国），要换成印尼盾（印度尼西亚）。规则：只允许相邻兑换：美国->日本->韩国->越南->印度尼西亚。请自动调用工具完成，并输出每一步和最终结果。"}
]
print(naive_run(messages))
