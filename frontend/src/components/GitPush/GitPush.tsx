import { useState } from 'react';
import { gitApi } from '../../services/api';
import './GitPush.css';

interface Props {
  testCaseId: string;
  defaultCommitMessage?: string;
  onPushed?: () => void;
}

export default function GitPush({ testCaseId, defaultCommitMessage, onPushed }: Props) {
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [token, setToken] = useState('');
  const [commitMessage, setCommitMessage] = useState(
    defaultCommitMessage || 'Add test case'
  );
  const [pushing, setPushing] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);

  const handlePush = async () => {
    if (!repoUrl || !branch || !token || !commitMessage) return;
    setPushing(true);
    setResult(null);
    try {
      await gitApi.push({
        repo_url: repoUrl,
        branch,
        token,
        commit_message: commitMessage,
        test_case_id: testCaseId,
      });
      setResult({ ok: true, message: 'Push 성공!' });
      onPushed?.();
    } catch (err: any) {
      setResult({
        ok: false,
        message: err?.response?.data?.detail || 'Push 실패. 입력 정보를 확인해 주세요.',
      });
    } finally {
      setPushing(false);
    }
  };

  return (
    <div className="git-push-panel">
      <div className="git-push-header">GitHub Push</div>
      <div className="git-push-form">
        <label>
          <span>저장소 URL</span>
          <input
            type="url"
            placeholder="https://github.com/user/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
          />
        </label>
        <label>
          <span>Branch</span>
          <input
            type="text"
            placeholder="main"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
          />
        </label>
        <label>
          <span>Personal Access Token</span>
          <input
            type="password"
            placeholder="ghp_xxxxxxxxxxxx"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
        </label>
        <label>
          <span>커밋 메시지</span>
          <textarea
            rows={2}
            value={commitMessage}
            onChange={(e) => setCommitMessage(e.target.value)}
          />
        </label>
        <button
          className="push-btn"
          onClick={handlePush}
          disabled={pushing || !repoUrl || !branch || !token || !commitMessage}
        >
          {pushing ? 'Pushing...' : 'Push to GitHub'}
        </button>
        {result && (
          <div className={`push-result ${result.ok ? 'success' : 'error'}`}>
            {result.message}
          </div>
        )}
      </div>
    </div>
  );
}
