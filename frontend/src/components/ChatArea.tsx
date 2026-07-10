import React, { useRef, useEffect } from 'react';
import type { Message } from '../types';
import MessageBubble from './MessageBubble';

interface Props {
  messages: Message[];
  showTrace: boolean;
  loading: boolean;
}

const ChatArea: React.FC<Props> = ({ messages, showTrace, loading }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="chat-area">
      {messages.length === 0 && (
        <div className="empty-state">
          <div className="icon">💬</div>
          <p>发送消息开始对话</p>
          <p className="hint">试试：帮我画一张饼图，展示三个部门的预算占比...</p>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} showTrace={showTrace} />
      ))}
      {loading && (
        <div className="loading">
          <div className="spinner" />
          思考中...
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
};

export default ChatArea;
