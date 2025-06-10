from openai import OpenAI

client = OpenAI(api_key="sk-1530b5812e634ccc873117cdb636b7c6", base_url="https://api.deepseek.com")

import sqlite3
from datetime import datetime

# 初始化数据库连接
conn = sqlite3.connect('subject_history.db')
c = conn.cursor()

# 创建消息表
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              role TEXT,
              content TEXT,
              timestamp DATETIME)''')
conn.commit()

# 加载最近5条历史记录
c.execute("SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT 5")
history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
messages = history if history else [{"role": "system", "content": "You are a helpful assistant"}]

# 认知教练系统提示词
COACH_PROMPT = '''
你作为深度认知教练，拥有跨学科思维模型工具箱。用户当前状态：
{current_status}  长期愿景：{user_vision}

### 核心任务
1. **认知镜像**：用苏格拉底式提问暴露用户思维盲区
2. **目标解构**：将模糊愿景分解为可验证里程碑（SMART原则）
3. **抗弃坑策略**：当检测到目标偏离时，启动环境改造方案

### 记忆交互
- 每次提取[记忆库]中最近3次对话的决策记录
- 当前对话结束前，必须生成：
  {
    "insight":"本次核心认知突破",
    "action_step":"未来72小时可执行任务",
    "risk_prediction":"可能遇到的3类阻力及预案"
  }

### 对话规则
⚠️ 禁止直接给答案！用以下工具引导用户自发现：
• 二阶思维模型：“如果这么做，接下来会发生什么？”
• 代价计算器：“达成此目标需牺牲什么？是否愿意支付？”
• 反事实推演：“假如5年后失败，最可能因为什么？”
'''

# 初始化时获取用户状态
current_status = input("当前状态描述（例：工作倦怠/学习瓶颈）：")
user_vision = input("长期愿景（例：3年成为AI专家）：")

messages = [
    {"role": "system", "content": COACH_PROMPT.format(
        current_status=current_status,
        user_vision=user_vision
    )}
]

while True:
    user_input = input("用户：")
    
    # 保存用户消息
    c.execute("INSERT INTO messages (role, content, timestamp) VALUES (?,?,?)",
              ("user", user_input, datetime.now()))
    conn.commit()
    
    # 获取助手回复
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages[-6:],  # 保留最近5轮+当前
        stream=False
    )
    
    # 保存助手回复
    assistant_reply = response.choices[0].message.content
    c.execute("INSERT INTO messages (role, content, timestamp) VALUES (?,?,?)",
              ("assistant", assistant_reply, datetime.now()))
    conn.commit()
    
    print(f"助手：{assistant_reply}")
    messages.append({"role": "assistant", "content": assistant_reply})