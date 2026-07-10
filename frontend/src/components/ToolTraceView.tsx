import React from 'react';
import type { ToolTrace } from '../types';

interface Props {
  trace: ToolTrace;
  defaultOpen?: boolean;
}

const ToolTraceView: React.FC<Props> = ({ trace, defaultOpen = false }) => {
  const [open, setOpen] = React.useState(defaultOpen);

  const fmt = (v: unknown): string => {
    if (typeof v === 'string') return v;
    try { return JSON.stringify(v, null, 2); }
    catch { return String(v); }
  };

  let resultDisplay: string;
  try { resultDisplay = JSON.stringify(JSON.parse(trace.result), null, 2); }
  catch { resultDisplay = trace.result; }

  return (
    <div className={`tool-trace${open ? ' open' : ''}`}>
      <div className="trace-header" onClick={() => setOpen(!open)}>
        <span className="arrow">▶</span>
        🔍 工具调用: <strong>{trace.tool_name}</strong>
      </div>
      {open && (
        <div className="trace-body">
          <div className="trace-col">
            <h4>📥 参数</h4>
            <pre>{fmt(trace.arguments)}</pre>
          </div>
          <div className="trace-col">
            <h4>📤 结果</h4>
            <pre>{resultDisplay}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolTraceView;
