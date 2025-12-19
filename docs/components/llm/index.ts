/**
 * Unified LLM interface exports.
 */

export type { LLMBackend, LLMBackendStatus, Message, StreamEvent } from './backend';
export { BackendRegistry } from './backend';
export { ClaudeBackend } from './claude-backend';
export { LocalLLMBackend, AVAILABLE_MODELS, type ModelId } from './local-backend';
