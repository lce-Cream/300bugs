import React, { useState, useRef, useEffect } from 'react';
import Markdown from 'marked-react';

function generateSessionId() {
  return Math.random().toString(36).substr(2, 9) + Date.now();
}

type ChatMessage = {
  sender: 'user' | 'bot';
  text?: string; // plain text
  markdown?: string; // markdown content from backend
  image?: string; // base64 image string
  sessionId?: string;
};

const ChatWithBot: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const sessionId = useRef<string>(generateSessionId());

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws/chat');

    ws.current.onmessage = (event) => {
      let parsed: any = null;
      try {
        parsed = JSON.parse(event.data);
      } catch (e) {
        const md = String(event.data);
        setMessages((prev) => [...prev, { sender: 'bot', markdown: md }]);
        return;
      }

      // If parsed JSON, support several shapes:
      // 1) { sender: 'bot'|'user', text: '...', markdown: '...' }
      // 2) { type: 'markdown', content: '...' }
      // 3) { content: '...', role: 'assistant' }

      if (parsed === null) return;

      // If image key is present, treat as base64 image
      if (parsed.image) {
        // Try to auto-detect MIME type from base64 header
        let mime = 'image/png';
        if (parsed.image.startsWith('/9j/')) mime = 'image/jpeg';
        if (parsed.image.startsWith('R0lGOD')) mime = 'image/gif';
        setMessages((prev) => [...prev, {
          sender: parsed.sender === 'user' ? 'user' : 'bot',
          image: parsed.image,
          sessionId: parsed.sessionId,
          // @ts-ignore
          mime,
        }]);
        // Debug log
        console.log('Received image base64:', parsed.image.slice(0, 40), '...');
        return;
      }

      // Prefer explicit markdown field
      if (parsed.markdown) {
        setMessages((prev) => [...prev, { sender: parsed.sender === 'user' ? 'user' : 'bot', markdown: parsed.markdown, sessionId: parsed.sessionId }]);
        return;
      }

      // If the server uses a type/content shape
      if (parsed.type === 'markdown' && parsed.content) {
        setMessages((prev) => [...prev, { sender: 'bot', markdown: parsed.content, sessionId: parsed.sessionId }]);
        return;
      }

      // If plain text field exists
      if (parsed.text) {
        setMessages((prev) => [...prev, { sender: parsed.sender === 'user' ? 'user' : 'bot', text: parsed.text, sessionId: parsed.sessionId }]);
        return;
      }

      // Fallback: if object has a 'content' field, treat as markdown
      if (parsed.content) {
        setMessages((prev) => [...prev, { sender: parsed.sender === 'user' ? 'user' : 'bot', markdown: String(parsed.content), sessionId: parsed.sessionId }]);
        return;
      }

      // Unknown shape - push as textified JSON for debugging
      setMessages((prev) => [...prev, { sender: 'bot', text: JSON.stringify(parsed) }]);
    };

    ws.current.onopen = () => {
      console.log('WebSocket connected');
    };
    ws.current.onclose = () => {
      console.log('WebSocket closed');
    };
    ws.current.onerror = (ev) => {
      console.warn('WebSocket error', ev);
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  const sendMessage = () => {
    if (input.trim() && ws.current?.readyState === 1) {
      const msg: ChatMessage = {
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
            <span className="chat-sender">{msg.sender === 'user' ? 'You' : 'Bot'}:</span>
            <div style={{ marginTop: 6 }}>
              {msg.image ? (
                <img
                  src={`data:image/png;base64,${msg.image}`}
                  // alt="chat image"
                  // style={{maxWidth:'300px',borderRadius:8}}
                />
              ) : msg.markdown ? (
                <Markdown>{msg.markdown}</Markdown>
              ) : (
                <Markdown>{msg.text}</Markdown>
              )}
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, width: '100%', marginTop: 12 }}>
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
