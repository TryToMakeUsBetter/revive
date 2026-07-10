import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import { fetchTools, fetchPrompts, sendMessage, resetChat, savePrompt, deletePrompt } from './api';
import type { Message, ToolTrace, Prompt } from './types';
import './App.css';

let msgIdCounter = 0;
function nextId() { return `msg-${++msgIdCounter}`; }

const App: React.FC = () => {
  const [model, setModel] = useState('加载中...');
  const [tools, setTools] = useState<string[]>([]);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [activePromptId, setActivePromptId] = useState<string | null>(null);
  const [promptName, setPromptName] = useState('');
  const [promptText, setPromptText] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [useTools, setUseTools] = useState(true);
  const [showTrace, setShowTrace] = useState(true);
  const [toolCallCount, setToolCallCount] = useState(0);

  // 选中的提示词内容（首次对话时发送）
  const promptContentRef = useRef<string | undefined>(undefined);

  // 初始化：获取工具列表和提示词列表
  useEffect(() => {
    fetchTools()
      .then((data) => {
        setModel(data.model);
        setTools(data.tools);
      })
      .catch(() => setModel('连接失败'));

    fetchPrompts()
      .then((data) => {
        setPrompts(data.prompts);
        if (data.active) setActivePromptId(data.active);
      })
      .catch(() => {});
  }, []);

  const handleSelectPrompt = useCallback((promptId: string | null) => {
    setActivePromptId(promptId);
    if (promptId) {
      const p = prompts.find((pp) => pp.id === promptId);
      const name = p?.name ?? '';
      const text = p?.content ?? '';
      setPromptName(name);
      setPromptText(text);
      promptContentRef.current = text;
    } else {
      setPromptName('');
      setPromptText('');
      promptContentRef.current = undefined;
    }
  }, [prompts]);

  const handlePromptNameChange = useCallback((name: string) => {
    setPromptName(name);
    if (activePromptId) {
      const p = prompts.find((pp) => pp.id === activePromptId);
      if (p?.name !== name) {
        setActivePromptId(null);
      }
    }
  }, [activePromptId, prompts]);

  const handlePromptTextChange = useCallback((text: string) => {
    setPromptText(text);
    promptContentRef.current = text || undefined;
    if (activePromptId) {
      const p = prompts.find((pp) => pp.id === activePromptId);
      if (p?.content !== text) {
        setActivePromptId(null);
      }
    }
  }, [activePromptId, prompts]);

  const handleSavePrompt = useCallback(async () => {
    const name = promptName.trim();
    const text = promptText.trim();
    if (!text) return;
    const finalName = name || text.split('\n')[0].replace(/^#\s*/, '').trim().slice(0, 30) || '自定义提示词';

    try {
      const data = await savePrompt(finalName, text);
      setPrompts(data.prompts);
      const saved = data.prompts.find((p: Prompt) => p.name === finalName && p.custom);
      if (saved) {
        setActivePromptId(saved.id);
        setPromptName(saved.name);
        promptContentRef.current = saved.content;
      }
    } catch (err) {
      console.error('保存提示词失败:', err);
    }
  }, [promptName, promptText]);

  const handleDeletePrompt = useCallback(async () => {
    if (!activePromptId) return;
    try {
      const data = await deletePrompt(activePromptId);
      setPrompts(data.prompts);
      setActivePromptId(null);
      setPromptText('');
      promptContentRef.current = undefined;
    } catch (err) {
      console.error('删除提示词失败:', err);
    }
  }, [activePromptId]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: Message = { id: nextId(), role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      // 首次消息时附带选中的 system_prompt
      const isFirst = messages.length === 0;
      const data = await sendMessage(
        text,
        useTools,
        isFirst ? promptContentRef.current : undefined,
      );
      // 首条消息发出后清除（后续消息不再重复发送 system_prompt）
      if (isFirst) promptContentRef.current = undefined;

      const traces: ToolTrace[] = data.tool_traces || [];
      const charts: string[] = data.charts || [];

      const assistantMsg: Message = {
        id: nextId(),
        role: 'assistant',
        content: data.reply,
        toolTraces: traces.length > 0 ? traces : undefined,
        charts: charts.length > 0 ? charts : undefined,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setToolCallCount((c) => c + traces.length);
    } catch (err) {
      const errorMsg: Message = {
        id: nextId(),
        role: 'assistant',
        content: `❌ 请求失败: ${err instanceof Error ? err.message : String(err)}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [useTools, messages.length]);

  const handleReset = useCallback(async () => {
    await resetChat();
    setMessages([]);
    setToolCallCount(0);
    setActivePromptId(null);
    setPromptName('');
    setPromptText('');
    promptContentRef.current = undefined;
    msgIdCounter = 0;
  }, []);

  return (
    <>
      <Sidebar
        model={model}
        tools={tools}
        prompts={prompts}
        activePromptId={activePromptId}
        promptName={promptName}
        promptText={promptText}
        useTools={useTools}
        showTrace={showTrace}
        messageCount={messages.length}
        toolCallCount={toolCallCount}
        onSelectPrompt={handleSelectPrompt}
        onPromptNameChange={handlePromptNameChange}
        onPromptTextChange={handlePromptTextChange}
        onSavePrompt={handleSavePrompt}
        onDeletePrompt={handleDeletePrompt}
        onToggleTools={setUseTools}
        onToggleTrace={setShowTrace}
        onReset={handleReset}
      />
      <div className="main">
        <div className="header">
          <h1>🤖 revive Chat</h1>
          <p>支持 DeepSeek / OpenAI 多轮对话 + Function Calling 工具调用</p>
        </div>
        <ChatArea messages={messages} showTrace={showTrace} loading={loading} />
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </>
  );
};

export default App;
