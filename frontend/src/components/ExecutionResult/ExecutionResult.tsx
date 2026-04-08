import { useState } from 'react';
import type { ExecutionResult as ExecResult, ExecutionStatus } from '../../services/types';
import './ExecutionResult.css';

interface Props {
  status: ExecutionStatus | null;
  result: ExecResult | null;
}

const STATUS_TEXT: Record<string, string> = {
  QUEUED: '대기중',
  RUNNING: '실행중',
  COMPLETED: '완료',
  FAILED: '실패',
  ABORTED: '중단됨',
};

const STEP_ICONS: Record<string, string> = {
  PASSED: 'V',
  FAILED: 'X',
  SKIPPED: '-',
};

export default function ExecutionResult({ status, result }: Props) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);
  const [showScreenshot, setShowScreenshot] = useState<string | null>(null);

  if (!status && !result) return null;

  // Running state
  if (status && !result) {
    const progressParts = status.progress?.split('/');
    const current = progressParts ? parseInt(progressParts[0]) : 0;
    const total = progressParts ? parseInt(progressParts[1]) : 0;
    const pct = total > 0 ? (current / total) * 100 : 0;

    return (
      <div className="execution-panel">
        <div className="exec-header running">
          <span>{STATUS_TEXT[status.status] || status.status}</span>
          {status.progress && <span>{status.progress} 스텝</span>}
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        </div>
        {status.current_step && (
          <div className="current-step">
            현재: <strong>{status.current_step}</strong>
          </div>
        )}
      </div>
    );
  }

  if (!result) return null;

  const { summary, steps } = result;
  const isSuccess = summary.failed === 0 && !summary.aborted;

  return (
    <div className="execution-panel">
      <div className={`exec-header ${isSuccess ? 'success' : 'failure'}`}>
        <span>{isSuccess ? '테스트 성공' : '테스트 실패'}</span>
        <span className="exec-duration">
          {result.total_duration_sec.toFixed(1)}초
        </span>
      </div>

      <div className="exec-summary">
        <div className="summary-item passed">
          통과 <strong>{summary.passed}</strong>
        </div>
        <div className="summary-item failed">
          실패 <strong>{summary.failed}</strong>
        </div>
        <div className="summary-item total">
          전체 <strong>{summary.total_steps}</strong>
        </div>
      </div>

      {summary.abort_reason && (
        <div className="abort-reason">중단 사유: {summary.abort_reason}</div>
      )}

      <div className="steps-timeline">
        {steps.map((step, i) => (
          <div key={i} className={`step-item ${step.status.toLowerCase()}`}>
            <div
              className="step-header"
              onClick={() => setExpandedStep(expandedStep === i ? null : i)}
            >
              <span className={`step-icon ${step.status.toLowerCase()}`}>
                {STEP_ICONS[step.status]}
              </span>
              <span className="step-name">{step.name}</span>
              <span className="step-duration">{step.duration_sec.toFixed(1)}s</span>
              {step.error_type && (
                <span className="step-error-badge">{step.error_type}</span>
              )}
            </div>
            {expandedStep === i && (
              <div className="step-detail">
                <div className="step-log">
                  <pre>{step.log}</pre>
                </div>
                {step.screenshot_url && (
                  <div className="step-screenshot">
                    <img
                      src={step.screenshot_url}
                      alt={`Step ${i + 1} screenshot`}
                      onClick={() => setShowScreenshot(step.screenshot_url!)}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {result.crash_logs.length > 0 && (
        <div className="crash-logs">
          <div className="crash-logs-title">Crash Logs</div>
          {result.crash_logs.map((log, i) => (
            <pre key={i} className="crash-log-item">{log}</pre>
          ))}
        </div>
      )}

      {result.device_info && (
        <div className="exec-device-info">
          {result.device_info.model} | Android {result.device_info.android_version} | {result.device_info.resolution}
        </div>
      )}

      {showScreenshot && (
        <div className="screenshot-modal" onClick={() => setShowScreenshot(null)}>
          <img src={showScreenshot} alt="Screenshot" />
        </div>
      )}
    </div>
  );
}
