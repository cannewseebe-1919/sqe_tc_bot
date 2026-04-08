import { useState, useEffect, useRef } from 'react';
import { ChatPanel } from '../components/Chat';
import { CodeEditor } from '../components/CodeEditor';
import { DeviceSelector } from '../components/DeviceSelector';
import { ExecutionResult } from '../components/ExecutionResult';
import { GitPush } from '../components/GitPush';
import { executionApi, createExecutionSocket, authApi } from '../services/api';
import type {
  Device,
  ExecutionStatus,
  ExecutionResult as ExecResultType,
  User,
} from '../services/types';
import './MainPage.css';

export default function MainPage() {
  const [user, setUser] = useState<User | null>(null);
  const [code, setCode] = useState('');
  const [testCaseId, setTestCaseId] = useState<string>('');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [execStatus, setExecStatus] = useState<ExecutionStatus | null>(null);
  const [execResult, setExecResult] = useState<ExecResultType | null>(null);
  const [rightTab, setRightTab] = useState<'device' | 'result' | 'git'>('device');
  const [executing, setExecuting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    authApi.getCurrentUser().then(({ data }) => setUser(data)).catch(() => {});
  }, []);

  const handleCodeGenerated = (newCode: string) => {
    setCode(newCode);
    setExecResult(null);
    setExecStatus(null);
    setExecutionId(null);
    setRightTab('device');
  };

  const handleExecute = async () => {
    if (!code || !selectedDevice || !user) return;
    setExecuting(true);
    setExecResult(null);
    setExecStatus(null);
    setRightTab('result');

    try {
      const { data } = await executionApi.start({
        test_code: code,
        device_id: selectedDevice.id,
        requested_by: user.email,
        callback_url: `${window.location.origin}/api/execution-result`,
      });
      setExecutionId(data.execution_id);
      setExecStatus({
        execution_id: data.execution_id,
        status: data.status,
        progress: '0/0',
      });

      // WebSocket for real-time status
      const ws = createExecutionSocket(data.execution_id);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'status') {
          setExecStatus(msg.data as ExecutionStatus);
        } else if (msg.type === 'result') {
          setExecResult(msg.data as ExecResultType);
          setExecStatus(null);
          setExecuting(false);
          ws.close();
        }
      };

      ws.onerror = () => {
        // Fallback to polling
        pollStatus(data.execution_id);
        ws.close();
      };

      ws.onclose = () => {
        wsRef.current = null;
      };
    } catch {
      setExecuting(false);
      alert('실행 요청에 실패했습니다.');
    }
  };

  const pollStatus = async (execId: string) => {
    const interval = setInterval(async () => {
      try {
        const { data } = await executionApi.getStatus(execId);
        setExecStatus(data);
        if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'ABORTED') {
          clearInterval(interval);
          const resultResp = await executionApi.getResult(execId);
          setExecResult(resultResp.data);
          setExecStatus(null);
          setExecuting(false);
        }
      } catch {
        clearInterval(interval);
        setExecuting(false);
      }
    }, 2000);
  };

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const canExecute = !!code && !!selectedDevice && !executing;

  return (
    <div className="main-page">
      <header className="top-bar">
        <div className="top-bar-title">TC Generator</div>
        <div className="top-bar-user">
          {user ? (
            <>
              <span>{user.name}</span>
              <button className="logout-btn" onClick={() => authApi.logout().then(() => window.location.href = '/login')}>
                로그아웃
              </button>
            </>
          ) : (
            <a href="/login">로그인</a>
          )}
        </div>
      </header>

      <div className="main-content">
        {/* Left: Chat */}
        <div className="panel-chat">
          <ChatPanel onCodeGenerated={handleCodeGenerated} />
        </div>

        {/* Center: Code Editor */}
        <div className="panel-editor">
          <CodeEditor code={code} onChange={setCode} />
          <div className="editor-actions">
            <button
              className="execute-btn"
              onClick={handleExecute}
              disabled={!canExecute}
            >
              {executing ? '실행중...' : '실행'}
            </button>
            {execResult && (
              <button
                className="confirm-btn"
                onClick={() => setRightTab('git')}
              >
                Confirm & Push
              </button>
            )}
          </div>
        </div>

        {/* Right: Device / Result / Git */}
        <div className="panel-right">
          <div className="right-tabs">
            <button
              className={rightTab === 'device' ? 'active' : ''}
              onClick={() => setRightTab('device')}
            >
              단말
            </button>
            <button
              className={rightTab === 'result' ? 'active' : ''}
              onClick={() => setRightTab('result')}
              disabled={!execStatus && !execResult}
            >
              결과
            </button>
            <button
              className={rightTab === 'git' ? 'active' : ''}
              onClick={() => setRightTab('git')}
              disabled={!execResult}
            >
              Git Push
            </button>
          </div>
          <div className="right-body">
            {rightTab === 'device' && (
              <DeviceSelector
                selectedId={selectedDevice?.id ?? null}
                onSelect={setSelectedDevice}
              />
            )}
            {rightTab === 'result' && (
              <ExecutionResult status={execStatus} result={execResult} />
            )}
            {rightTab === 'git' && testCaseId && (
              <GitPush testCaseId={testCaseId} />
            )}
            {rightTab === 'git' && !testCaseId && (
              <GitPush testCaseId="" defaultCommitMessage={`Add TC: ${code.split('\n').find(l => l.includes('class '))?.trim() || 'test_case'}`} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
