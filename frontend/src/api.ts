import type { ChatResponse, ToolsResponse, PromptsResponse } from './types';

const BASE = '';  // Vite proxy handles /api → backend

export async function fetchTools(): Promise<ToolsResponse> {
  const res = await fetch(`${BASE}/api/tools`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchPrompts(): Promise<PromptsResponse> {
  const res = await fetch(`${BASE}/api/prompts`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function savePrompt(name: string, content: string): Promise<PromptsResponse> {
  const res = await fetch(`${BASE}/api/prompts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function deletePrompt(promptId: string): Promise<PromptsResponse> {
  const res = await fetch(`${BASE}/api/prompts/${promptId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function sendMessage(
  message: string,
  useTools: boolean,
  systemPrompt?: string,
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, use_tools: useTools, system_prompt: systemPrompt || undefined }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function resetChat(): Promise<void> {
  await fetch(`${BASE}/api/reset`, { method: 'POST' });
}
