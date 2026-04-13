import { useState, useEffect } from 'react';
import { ChatPanel } from '../components/Chat';
import { CodeEditor } from '../components/CodeEditor';
import { ExecutionPanel } from '../components/ExecutionPanel';
import { authApi } from '../services/api';
import type { User } from '../services/types';
import './MainPage.css';

export default function MainPage() {
  const [user, setUser] = useState<User | null>(null);
  const [code, setCode] = useState('');
  const [testCaseId, setTestCaseId] = useState<string>('');
  const [codeVersion, setCodeVersion] = useState(0);

  useEffect(() => {
    authApi.getCurrentUser().then(({ data }) => setUser(data)).catch(() => {});
  }, []);

  const handleCodeGenerated = (newCode: string, newTestCaseId?: string) => {
    setCode(newCode);
    setTestCaseId(newTestCaseId ?? '');
    setCodeVersion(v => v + 1);
  };

  return (
    <div className="main-page">
      <header className="top-bar">
        <div className="top-bar-title">TC Generator</div>
        <div className="top-bar-user">
          {user ? (
            <>
              <span>{user.name}</span>
              <button
                className="logout-btn"
                onClick={() => authApi.logout().then(() => (window.location.href = '/login'))}
              >
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
        </div>

        {/* Right: Execution Panel */}
        <div className="panel-right">
          <ExecutionPanel
            code={code}
            user={user}
            testCaseId={testCaseId}
            resetKey={codeVersion}
          />
        </div>
      </div>
    </div>
  );
}
