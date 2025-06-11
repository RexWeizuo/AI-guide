const messageContainer = document.getElementById('message-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

// 消息创建函数
function createMessage(content, isUser = false) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
  messageDiv.innerHTML = `<div class="content">${content}</div>`;
  return messageDiv;
}

// 发送消息处理
sendBtn.addEventListener('click', async () => {
  const content = userInput.value.trim();
  if (!content) return;

  // 添加用户消息
  messageContainer.appendChild(createMessage(content, true));
  userInput.value = '';

  // 调用后端API
  try {
    const response = await fetch('http://localhost:5000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: content })
    });
    
    const data = await response.json();
    const aiResponse = createMessage(data.reply);
    messageContainer.appendChild(aiResponse);
    aiResponse.scrollIntoView({ behavior: 'smooth' });
  } catch (error) {
    console.error('API请求失败:', error);
    messageContainer.appendChild(createMessage('服务暂时不可用，请稍后重试'));
  }
});

// 回车发送支持
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});