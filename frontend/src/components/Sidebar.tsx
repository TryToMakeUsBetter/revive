import React from 'react';
import type { Prompt } from '../types';

interface Props {
  model: string;
  tools: string[];
  prompts: Prompt[];
  activePromptId: string | null;
  promptName: string;
  promptText: string;
  useTools: boolean;
  showTrace: boolean;
  messageCount: number;
  toolCallCount: number;
  onSelectPrompt: (promptId: string | null) => void;
  onPromptNameChange: (name: string) => void;
  onPromptTextChange: (text: string) => void;
  onSavePrompt: () => void;
  onDeletePrompt: () => void;
  onToggleTools: (v: boolean) => void;
  onToggleTrace: (v: boolean) => void;
  onReset: () => void;
}

const Sidebar: React.FC<Props> = ({
  model, tools, prompts, activePromptId, promptName, promptText,
  useTools, showTrace, messageCount, toolCallCount,
  onSelectPrompt, onPromptNameChange, onPromptTextChange,
  onSavePrompt, onDeletePrompt,
  onToggleTools, onToggleTrace, onReset,
}) => {
  const isCustomPrompt = activePromptId?.startsWith('custom_');

  return (
    <aside className="sidebar">
      <h2>⚙️ 配置</h2>
      <div className="model-info">
        模型: <code>{model}</code>
      </div>

      {/* ── 提示词选择 ── */}
      <div>
        <h2>📝 系统提示词</h2>
        <select
          className="prompt-select"
          value={activePromptId ?? ''}
          onChange={(e) => onSelectPrompt(e.target.value || null)}
        >
          <option value="">（自定义）</option>
          <optgroup label="内置">
            {prompts.filter(p => !p.custom).map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </optgroup>
          <optgroup label="我的提示词">
            {prompts.filter(p => p.custom).map((p) => (
              <option key={p.id} value={p.id}>📌 {p.name}</option>
            ))}
          </optgroup>
        </select>
        <input
          className="prompt-name-input"
          type="text"
          value={promptName}
          onChange={(e) => onPromptNameChange(e.target.value)}
          placeholder="提示词名称"
          spellCheck={false}
        />
        <textarea
          className="prompt-textarea"
          value={promptText}
          onChange={(e) => onPromptTextChange(e.target.value)}
          placeholder="输入系统提示词（可选，首条消息时生效）..."
          rows={4}
          spellCheck={false}
        />
        <div className="prompt-actions">
          <button
            className="btn-sm btn-save"
            onClick={onSavePrompt}
            disabled={!promptText.trim()}
            title="保存为自定义提示词"
          >💾 保存</button>
          {isCustomPrompt && (
            <button
              className="btn-sm btn-delete"
              onClick={onDeletePrompt}
              title="删除此提示词"
            >🗑 删除</button>
          )}
        </div>
      </div>

      <label>
        <input
          type="checkbox"
          checked={useTools}
          onChange={(e) => onToggleTools(e.target.checked)}
        />
        启用 Tool Use
      </label>

      <label>
        <input
          type="checkbox"
          checked={showTrace}
          onChange={(e) => onToggleTrace(e.target.checked)}
        />
        显示工具调用详情
      </label>

      <button onClick={onReset}>🔄 重置对话</button>

      <div>
        <h2>🔧 已注册工具</h2>
        <div className="tools-list">
          {tools.length > 0
            ? tools.map((t) => <code key={t}>{t}</code>)
            : <span className="dim">（无）</span>}
        </div>
      </div>

      <div className="stats">
        消息数: {messageCount} &nbsp;|&nbsp; 工具调用: {toolCallCount}
      </div>
    </aside>
  );
};

export default Sidebar;
