import axios from 'axios';
import type {
  ChatMessage,
  Device,
  ExecutionRequest,
  ExecutionResponse,
  ExecutionStatus,
  ExecutionResult,
  GitPushRequest,
  User,
} from './types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Auth
export const authApi = {
  getLoginUrl: () => api.get<{ url: string }>('/auth/saml/login'),
  getCurrentUser: () => api.get<User>('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

// Chat
export const chatApi = {
  sendMessage: (message: string, attachments?: File[]) => {
    const formData = new FormData();
    formData.append('message', message);
    if (attachments) {
      attachments.forEach((f) => formData.append('files', f));
    }
    return api.post<ChatMessage>('/chat', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getHistory: (sessionId: string) =>
    api.get<ChatMessage[]>(`/chat/history/${sessionId}`),
};

// Test Case
export const testCaseApi = {
  get: (id: string) => api.get(`/testcase/${id}`),
  update: (id: string, code: string) =>
    api.put(`/testcase/${id}`, { code }),
  confirm: (id: string) => api.post(`/testcase/${id}/confirm`),
};

// Devices (from Test Executor)
const executorApi = axios.create({
  baseURL: import.meta.env.VITE_EXECUTOR_API_URL || '/executor-api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

export const deviceApi = {
  list: () => executorApi.get<{ devices: Device[] }>('/api/devices'),
};

// Execution
export const executionApi = {
  start: (req: ExecutionRequest) =>
    executorApi.post<ExecutionResponse>('/api/execute', req),
  getStatus: (executionId: string) =>
    executorApi.get<ExecutionStatus>(`/api/execute/${executionId}/status`),
  getResult: (executionId: string) =>
    api.get<ExecutionResult>(`/execution/${executionId}/result`),
};

// Git Push
export const gitApi = {
  push: (req: GitPushRequest) => api.post('/git/push', req),
};

// WebSocket for execution streaming
export function createExecutionSocket(executionId: string): WebSocket {
  const wsBase =
    import.meta.env.VITE_EXECUTOR_WS_URL ||
    `ws://${window.location.hostname}:8001`;
  return new WebSocket(`${wsBase}/api/execute/${executionId}/stream`);
}

export { api, executorApi };
