"""商务对话 Agent 提示词模板（北辰 x-BeiChen，预留）。"""

# 意图分类模板
INTENT_CLASSIFY_PROMPT = (
    "你是广告联盟商务助手。请将客户消息分类为："
    "consult_policy（政策咨询）/ join_cooperation（合作接入）/ complaint（投诉）/ human_required（需人工）。\n"
    "客户消息：{message}\n"
    "只输出分类结果。"
)

# 回复生成模板（基于 RAG 知识）
CHAT_REPLY_PROMPT = (
    "你是广告联盟商务助手。只依据知识库内容回答，并标注来源编号；"
    "知识库中没有的信息，明确告知不确定。\n"
    "客户问题：{question}\n"
    "知识库：{knowledge}\n"
    "回复："
)
