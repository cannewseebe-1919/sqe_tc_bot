import { useState, useEffect, useRef } from 'react';
import { DeviceSelector } from '../DeviceSelector';
import { ExecutionResult } from '../ExecutionResult';
import { GitPush } from '../GitPush';
import { executionApi, createExecutionSocket } from '../../services/api';
import type {
  Device,
  ExecutionStatus,
  ExecutionResult as ExecResultType,
  User,
} from '../../services/types';
import './ExecutionPanel.css';

interface Props {
  code: string;
  user: User | null;
  testCaseId?: string;
  resetKey?: number;
}

export default function ExecutionPanel({ code, user, testCaseId, resetKey }: Props) {
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [executing, setExecuting] = useState(false);
  const [execStatus, setExecStatus] = useState<ExecutionStatus | null>(null);
  const [execResult, setExecResult] = useState<ExecResultType | null>(null);
  const [showGitPush, setShowGitPush] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 새 코드가 생성될 때 상태 초기화
  useEffect(() => {
    wsRef.current?.close();
    setExecResult(null);
    setExecStatus(null);
    setExecuting(false);
    setShowGitPush(false);
  }, [resetKey]);

  const handleExecute = async () => {
    if (!code || !selectedDevice || !user) return;
    setExecuting(true);
    setExecResult(null);
    setExecStatus(null);
    setShowGitPush(false);

    try {
      const { data } = await executionApi.start({
        test_code: code,
        device_id: selectedDevice.id,
        requested_by: user.email,
        callback_url: `${window.location.origin}/api/execution-result`,
      });

      setExecStatus({
        execution_id: data.execution_id,
        status: data.status,
        progress: '0/0',
      });

      const ws = createExecutionSocket(data.execution_id);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'status') {
            setExecStatus(msg.data as ExecutionStatus);
          } else if (msg.type === 'result') {
            setExecResult(msg.data as ExecResultType);
            setExecStatus(null);
            setExecuting(false);
            ws.close();
          }
        } catch {
          pollStatus(data.execution_id);
          ws.close();
        }
      };

      ws.onerror = () => {
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

  const pollStatus = (execId: string) => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(async () => {
      try {
        const { data } = await executionApi.getStatus(execId);
        setExecStatus(data);
        if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'ABORTED') {
          clearInterval(intervalRef.current!);
          intervalRef.current = null;
          const resultResp = await executionApi.getResult(execId);
          setExecResult(resultResp.data);
          setExecStatus(null);
          setExecuting(false);
        }
      } catch {
        clearInterval(intervalRef.current!);
        intervalRef.current = null;
        setExecuting(false);
      }
    }, 2000);
  };

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const canExecute = !!code && !!selectedDevice && !executing;
  const commitMessage = `Add TC: ${code.split('\n').find(l => l.includes('class '))?.trim() || 'test_case'}`;

  return (
    <div className="execution-panel-wrap">
      {/* 단말 선택 */}
      <section className="ep-section">
        <DeviceSelector
          selectedId={selectedDevice?.id ?? null}
          onSelect={setSelectedDevice}
        />
      </section>

      {/* 실행 버튼 */}
      <section className="ep-section ep-run-section">
        <button
          className="ep-run-btn"
          onClick={handleExecute}
          disabled={!canExecute}
        >
          {executing ? '실행중...' : '▶ 실행'}
        </button>
        {!selectedDevice && (
          <span className="ep-run-hint">단말을 선택하면 실행할 수 있습니다</span>
        )}
      </section>

      {/* 진행 상황 / 결과 */}
      {(execStatus || execResult) && (
        <section className="ep-section">
          <ExecutionResult status={execStatus} result={execResult} />
        </section>
      )}

      {/* Git Push */}
      {execResult && (
        <section className="ep-section ep-git-section">
          <button
            className="ep-git-toggle"
            onClick={() => setShowGitPush(v => !v)}
          >
            {showGitPush ? '▲ Git Push 닫기' : '▼ Git Push'}
          </button>
          {showGitPush && (
            <GitPush
              testCaseId={testCaseId ?? ''}
              defaultCommitMessage={commitMessage}
            />
          )}
        </section>
      )}
    </div>
  );
}
