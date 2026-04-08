import { useState, useRef, useEffect } from 'react';
import ChatInput from './ChatInput';
import ChatMessageComponent from './ChatMessage';
import { chatApi } from '../../services/api';
import type { ChatMessage } from '../../services/types';
import './Chat.css';

interface Props {
  onCodeGenerated: (code: string) => void;
}

export default function ChatPanel({ onCodeGenerated }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'system-0',
      role: 'assistant',
      content:
        '안녕하세요! 테스트 케이스 생성 봇입니다. 어떤 테스트를 만들어 드릴까요?\nWord(.docx) 또는 PDF 파일을 드래그하여 첨부할 수도 있습니다.',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text: string, files: File[]) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
      attachments: files.map((f) => ({
        name: f.name,
        type: f.type,
        size: f.size,
      })),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const { data } = await chatApi.sendMessage(text, files.length > 0 ? files : undefined);
      setMessages((prev) => [...prev, data]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: '죄송합니다, 요청 처리 중 오류가 발생했습니다. 다시 시도해 주세요.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">TC Generator</div>
      <div className="chat-messages">
        {messages.map((m) => (
          <ChatMessageComponent
            key={m.id}
            message={m}
            onCodeGenerated={onCodeGenerated}
          />
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="message-avatar">AI</div>
            <div className="message-body">
              <div className="typing-indicator">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
