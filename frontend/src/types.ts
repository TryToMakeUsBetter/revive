/** 后端 API 返回的工具调用追踪 */
export interface ToolTrace {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: string;
}

/** POST /api/chat 响应 */
export interface ChatResponse {
  reply: string;
  tool_traces: ToolTrace[];
  charts: string[];
}

/** GET /api/tools 响应 */
export interface ToolsResponse {
  tools: string[];
  model: string;
}

/** 提示词 */
export interface Prompt {
  id: string;
  name: string;
  content: string;
  custom: boolean;  // 是否为用户自定义（可删除）
}

/** GET /api/prompts 响应 */
export interface PromptsResponse {
  prompts: Prompt[];
  active: string | null;
}

/** 对话消息 */
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolTraces?: ToolTrace[];
  charts?: string[];
}
