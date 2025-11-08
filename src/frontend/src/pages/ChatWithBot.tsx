import React, { useState, useRef, useEffect } from 'react';

function generateSessionId() {
  return Math.random().toString(36).substr(2, 9) + Date.now();
}

const ChatWithBot: React.FC = () => {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const sessionId = useRef<string>(generateSessionId());

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat');
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
    };
    return () => {
      ws.current?.close();
    };
  }, []);

  const sendMessage = () => {
    if (input.trim() && ws.current?.readyState === 1) {
      const msg = {
        text: input,
        sender: 'user',
        sessionId: sessionId.current,
      };
      ws.current.send(JSON.stringify(msg));
      setMessages((prev) => [...prev, msg]);
      setInput('');
    }
  };

  return (
    <div className="page-container">
      <h2>Chat with Bot</h2>
      <div className="chat-box">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={msg.sender === 'user' ? 'chat-message user-message' : 'chat-message bot-message'}
          >
            <span className="chat-sender">{msg.sender === 'user' ? 'You' : 'Bot'}:</span> {msg.text}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' ? sendMessage() : undefined}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default ChatWithBot;
