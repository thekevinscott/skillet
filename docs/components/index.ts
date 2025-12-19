export { Terminal } from './Terminal';
export type { TerminalRef } from './Terminal';
export { ClaudeTerminal } from './ClaudeTerminal';
export { LocalLLMTerminal } from './LocalLLMTerminal';
export { UnifiedTerminal } from './UnifiedTerminal';
export { ApiKeyInput } from './ApiKeyInput';
export { ClaudeClient } from './claude';
export { LocalLLMClient, AVAILABLE_MODELS } from './webllm';
export type { Message, ClaudeResponse, StreamEvent } from './claude';
export type { Message as LocalMessage, StreamEvent as LocalStreamEvent, ModelId } from './webllm';

// Unified LLM interface
export {
  BackendRegistry,
  ClaudeBackend,
  LocalLLMBackend,
} from './llm';
export type {
  LLMBackend,
  LLMBackendStatus,
  Message as UnifiedMessage,
  StreamEvent as UnifiedStreamEvent,
} from './llm';

// Reactive docs components
export { ReactiveDocsLayout, DocsPanel } from './reactive-docs';
export type { Tutorial, TutorialStep, TutorialState } from './reactive-docs';
export { helloWorldTutorial } from './reactive-docs/tutorials';
