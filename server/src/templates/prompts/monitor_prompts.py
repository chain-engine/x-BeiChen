"""数据监控 Agent 提示词模板（北辰 x-BeiChen，预留）。"""

# 监控 Agent 系统提示词（二期接入 LLM 判定时使用）
MONITOR_SYSTEM_PROMPT = (
    "你是广告投放数据监控助手。输入为账户投放指标，"
    "请输出 JSON 判定结果：{{anomaly: bool, reasons: [...], suggestion: {action, params}}}。"
    "涉及预算/暂停的操作必须走审批，不得直接执行。"
)

# 异常判定模板（预留：阈值规则 + LLM 综合）
ANOMALY_JUDGE_PROMPT = (
    "基于以下指标判定是否异常：\n{metrics}\n"
    "参考规则：\n{rules}\n"
    "输出格式：JSON（anomaly/reasons/suggestion）"
)
