import React from 'react';
import type { Message } from '../types';
import ToolTraceView from './ToolTraceView';
import ChartDisplay from './ChartDisplay';

interface Props {
  message: Message;
  showTrace: boolean;
}

const MessageBubble: React.FC<Props> = ({ message, showTrace }) => {
  const { role, content, toolTraces, charts } = message;

  const formatContent = (text: string) => {
    return text
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className={`msg ${role}`}>
      <div className="avatar">{role === 'user' ? '🧑' : '🤖'}</div>
      <div className="bubble">
        <div dangerouslySetInnerHTML={{ __html: formatContent(content) }} />

        {showTrace && toolTraces?.map((trace, i) => (
          <ToolTraceView
            key={i}
            trace={trace}
            defaultOpen={i === (toolTraces.length - 1)}
          />
        ))}

        {charts?.map((url, i) => (
          <ChartDisplay key={i} url={url} />
        ))}
      </div>
    </div>
  );
};

export default MessageBubble;
