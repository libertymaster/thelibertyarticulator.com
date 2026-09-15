import { Component, useEffect, type ErrorInfo, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { parsePayload, type Validator } from './lib';
import './islands.css';

class IslandBoundary extends Component<{ children: ReactNode; fallbackId: string }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error, _info: ErrorInfo) {
    const fallback = document.getElementById(this.props.fallbackId);
    if (fallback) fallback.hidden = false;
    console.error('Research tool unavailable:', error.message);
  }
  render() {
    return this.state.failed ? <p className="notice" role="status">The interactive tool is unavailable. The server-rendered content remains below.</p> : this.props.children;
  }
}
function Ready({ fallbackId, children }: { fallbackId: string; children: ReactNode }) {
  useEffect(() => {
    const fallback = document.getElementById(fallbackId);
    if (fallback) fallback.hidden = true;
    return () => { if (fallback) fallback.hidden = false; };
  }, [fallbackId]);
  return children;
}
export function mount<T>(id: string, validate: Validator, render: (data: T) => ReactNode) {
  const node = document.getElementById(id);
  if (!node) return;
  const payloadNode = document.getElementById(node.dataset.payload ?? '');
  const fallbackId = node.dataset.fallback ?? '';
  try {
    const data = parsePayload<T>(JSON.parse(payloadNode?.textContent ?? 'null'), validate);
    createRoot(node).render(<IslandBoundary fallbackId={fallbackId}><Ready fallbackId={fallbackId}>{render(data)}</Ready></IslandBoundary>);
  } catch (error) {
    // Never hide the fallback when parsing or schema validation fails.
    console.error('Research tool initialization failed:', error);
  }
}
