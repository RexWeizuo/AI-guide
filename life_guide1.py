import mysql.connector
from openai import OpenAI

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'chat_history'
}

# 初始化数据库连接
def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# 保存对话记录
def save_conversation(role, content):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (role, content) VALUES (%s, %s)",
        (role, content)
    )
    conn.commit()
    conn.close()

# 获取历史对话
def get_history():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM conversations ORDER BY created_at DESC LIMIT 10")
    history = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()
    return history

# 初始化数据库
init_db()

client = OpenAI(api_key="sk-1530b5812e634ccc873117cdb636b7c6", base_url="https://api.deepseek.com")

while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        break
    
    # 保存用户输入
    save_conversation('user', user_input)
    
    # 获取历史对话
    history = get_history()
    
    # 构建消息列表
    messages = [
        {"role": "system", "content": "You are my life guide."},
        *history,
        {"role": "user", "content": user_input}
    ]
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    
    ai_response = response.choices[0].message.content
    print("AI:", ai_response)
    
    # 保存AI回复
    save_conversation('assistant', ai_response)