// Device
export interface Device {
  id: string;
  name: string;
  status: 'CONNECTED' | 'TESTING' | 'QUEUED' | 'OFFLINE' | 'ERROR';
  model: string;
  android_version: string;
  queue_length: number;
}

// Chat
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  attachments?: FileAttachment[];
  code?: string;
}

export interface FileAttachment {
  name: string;
  type: string;
  size: number;
  file?: File;
}

// Test Case
export interface TestCase {
  id: string;
  title: string;
  code: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  source_type: 'chat' | 'file_upload';
  status: 'draft' | 'confirmed' | 'pushed';
  git_info?: GitInfo;
}

export interface GitInfo {
  repo_url: string;
  branch: string;
  commit_message: string;
  pushed_at?: string;
  pushed_by?: string;
}

// Execution
export interface ExecutionRequest {
  test_code: string;
  device_id: string;
  requested_by: string;
  callback_url: string;
}

export interface ExecutionResponse {
  execution_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ABORTED';
  queue_position: number;
}

export interface ExecutionStatus {
  execution_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ABORTED';
  current_step?: string;
  progress?: string;
  started_at?: string;
}

export interface ExecutionStep {
  name: string;
  status: 'PASSED' | 'FAILED' | 'SKIPPED';
  duration_sec: number;
  screenshot_url?: string;
  log: string;
  error_type?: ErrorType;
}

export type ErrorType =
  | 'ASSERTION_FAILED'
  | 'ELEMENT_NOT_FOUND'
  | 'STEP_TIMEOUT'
  | 'APP_CRASH'
  | 'ANR'
  | 'KERNEL_PANIC'
  | 'SYSTEM_UI_CRASH'
  | 'ADB_ERROR';

export interface ExecutionResult {
  execution_id: string;
  status: 'COMPLETED' | 'FAILED' | 'ABORTED';
  device_id: string;
  started_at: string;
  finished_at: string;
  total_duration_sec: number;
  summary: {
    total_steps: number;
    passed: number;
    failed: number;
    aborted: boolean;
    abort_reason?: string;
  };
  steps: ExecutionStep[];
  crash_logs: string[];
  device_info: {
    model: string;
    android_version: string;
    resolution: string;
  };
}

// Git Push
export interface GitPushRequest {
  repo_url: string;
  branch: string;
  token: string;
  commit_message: string;
  test_case_id: string;
}

// Auth
export interface User {
  email: string;
  name: string;
  department?: string;
}

// Chat API response (from backend)
export interface ChatResponse {
  reply: string;
  code?: string | null;
  test_case_id?: string | null;
  conversation_id: string;
}

// File upload response
export interface FileUploadResponse {
  filename: string;
  extracted_text: string;
  char_count: number;
}
