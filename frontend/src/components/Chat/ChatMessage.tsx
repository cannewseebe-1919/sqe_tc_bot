import type { ChatMessage as ChatMsg } from '../../services/types';
import './Chat.css';

interface Props {
  message: ChatMsg;
  onCodeGenerated?: (code: string) => void;
}

export default function ChatMessage({ message, onCodeGenerated }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-avatar">{isUser ? 'U' : 'AI'}</div>
      <div className="message-body">
        <div className="message-content">{message.content}</div>
        {message.attachments && message.attachments.length > 0 && (
          <div className="message-attachments">
            {message.attachments.map((a, i) => (
              <span key={i} className="file-chip readonly">{a.name}</span>
            ))}
          </div>
        )}
        {message.code && (
          <div className="message-code-block">
            <div className="code-header">
              <span>생성된 TC 코드</span>
              <button
                className="use-code-btn"
                onClick={() => onCodeGenerated?.(message.code!)}
              >
                에디터에서 열기
              </button>
            </div>
            <pre><code>{message.code}</code></pre>
          </div>
        )}
        <span className="message-time">
          {new Date(message.timestamp).toLocaleTimeString('ko-KR')}
        </span>
      </div>
    </div>
  );
}
