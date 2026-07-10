import React, { useState, useRef, useEffect } from 'react';

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

const ChatInput: React.FC<Props> = ({ onSend, disabled }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [text]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-area">
      <textarea
        ref={textareaRef}
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入消息..."
        disabled={disabled}
      />
      <button onClick={handleSend} disabled={disabled || !text.trim()} title="发送 (Enter)">
        ➤
      </button>
    </div>
  );
};

export default ChatInput;
