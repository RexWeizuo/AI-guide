from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from openai import OpenAI
import json
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)

# DeepSeek API配置
client = OpenAI(api_key="sk-1530b5812e634ccc873117cdb636b7c6", base_url="https://api.deepseek.com")

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'database': 'chatbot_db',
    'user': 'root',
    'password': 'twz990304'  # 请替换为你的MySQL密码
}

def init_database():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute("CREATE DATABASE IF NOT EXISTS chatbot_db")
        cursor.execute("USE chatbot_db")
        
        # 创建会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                title VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # 创建消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                role ENUM('user', 'assistant') NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session_id (session_id)
            )
        """)
        
        connection.commit()
        print("数据库初始化成功")
        
    except Error as e:
        print(f"数据库初始化错误: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        user_message = data.get('message')
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
            
        if not session_id:
            session_id = str(uuid.uuid4())
            # 创建新会话
            create_conversation(session_id, user_message[:50] + "...")
        
        # 保存用户消息到数据库
        save_message(session_id, 'user', user_message)
        
        # 获取历史对话记录
        history = get_conversation_history(session_id)
        
        # 构建OpenAI API请求的消息格式
        messages = []
        for msg in history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # 调用DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        
        ai_response = response.choices[0].message.content
        
        # 保存AI回复到数据库
        save_message(session_id, 'assistant', ai_response)
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"聊天处理错误: {e}")
        return jsonify({'error': '处理请求时发生错误'}), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取所有会话列表"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT session_id, title, created_at, updated_at 
            FROM conversations 
            ORDER BY updated_at DESC
        """)
        
        conversations = cursor.fetchall()
        
        # 转换datetime为字符串
        for conv in conversations:
            conv['created_at'] = conv['created_at'].isoformat()
            conv['updated_at'] = conv['updated_at'].isoformat()
        
        return jsonify(conversations)
        
    except Error as e:
        print(f"获取会话列表错误: {e}")
        return jsonify({'error': '获取会话列表失败'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/conversations/<session_id>/messages', methods=['GET'])
def get_conversation_messages(session_id):
    """获取指定会话的消息记录"""
    try:
        history = get_conversation_history(session_id)
        return jsonify(history)
        
    except Exception as e:
        print(f"获取会话消息错误: {e}")
        return jsonify({'error': '获取会话消息失败'}), 500

@app.route('/api/conversations/<session_id>', methods=['DELETE'])
def delete_conversation(session_id):
    """删除指定会话"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 删除消息记录
        cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
        # 删除会话记录
        cursor.execute("DELETE FROM conversations WHERE session_id = %s", (session_id,))
        
        connection.commit()
        
        return jsonify({'message': '会话删除成功'})
        
    except Error as e:
        print(f"删除会话错误: {e}")
        return jsonify({'error': '删除会话失败'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_conversation(session_id, title):
    """创建新会话"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (session_id, title) 
            VALUES (%s, %s)
        """, (session_id, title))
        
        connection.commit()
        
    except Error as e:
        print(f"创建会话错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_message(session_id, role, content):
    """保存消息到数据库"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO messages (session_id, role, content) 
            VALUES (%s, %s, %s)
        """, (session_id, role, content))
        
        connection.commit()
        
        # 更新会话的更新时间
        cursor.execute("""
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE session_id = %s
        """, (session_id,))
        
        connection.commit()
        
    except Error as e:
        print(f"保存消息错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_conversation_history(session_id, limit=50):
    """获取会话历史记录"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT role, content, timestamp 
            FROM messages 
            WHERE session_id = %s 
            ORDER BY timestamp ASC 
            LIMIT %s
        """, (session_id, limit))
        
        messages = cursor.fetchall()
        
        # 转换datetime为字符串
        for msg in messages:
            msg['timestamp'] = msg['timestamp'].isoformat()
        
        return messages
        
    except Error as e:
        print(f"获取会话历史错误: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 启动Flask应用
    app.run(host='127.0.0.1', port=5000, debug=True)