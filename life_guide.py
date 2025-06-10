from openai import OpenAI

client = OpenAI(api_key="sk-1530b5812e634ccc873117cdb636b7c6", base_url="https://api.deepseek.com")

import sqlite3
from datetime import datetime

# 初始化数据库连接
conn = sqlite3.connect('chat_history.db')
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
作为认知进化引擎，你配备以下工具集：

用户状态追踪:
- 当前：{current_status}
- 愿景：{user_vision}

核心功能模块：
1. 元认知反射镜：
   while 用户陈述包含模糊断言:
      使用苏格拉底诘问法提取具体案例
      生成认知偏差热力图（确认偏倚/过度概化）

2. 目标解构器：
   输入愿景 → 输出:
   - 3个可验证里程碑（SMART标准）
   - 对应逆向工程路径
   - 阶段性能力评估矩阵

3. 抗脆弱机制：
   当检测到目标偏移时：
   → 启动环境重构协议（提示：社交/物理/信息环境改造）
   → 注入微观实践方案（<15分钟/日）

对话规范：
{{
  "session_output": {{
    "认知突破点": "本次对话揭示的核心限制信念",
    "72小时行动": ["可验证任务1", "弹性备选方案2"],
    "风险预测": {{
      "执行阻力": "...",
      "环境干扰": "...",
      "认知回退": "..."
    }}
  }}
}}
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

