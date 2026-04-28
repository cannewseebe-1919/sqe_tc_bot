import { useEffect } from 'react';
import { authApi } from '../services/api';
import './LoginPage.css';

export default function LoginPage() {
  const handleLogin = async () => {
    try {
      const { data } = await authApi.getLoginUrl();
      window.location.href = data.url;
    } catch {
      alert('SSO 로그인 URL을 가져올 수 없습니다.');
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">TC</div>
        <h1>SQE TC Generator</h1>
        <p>AI 기반 테스트 케이스 자동 생성 플랫폼</p>
        <button className="sso-btn" onClick={handleLogin}>
          SSO 로그인
        </button>
        <span className="login-note">사내 계정으로 로그인하세요</span>
      </div>
    </div>
  );
}
