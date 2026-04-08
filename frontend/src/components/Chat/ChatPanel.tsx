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
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
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
      // 파일이 있으면 먼저 업로드해서 텍스트 추출
      let fileContent: string | undefined;
      if (files.length > 0) {
        const uploads = await Promise.all(files.map((f) => chatApi.uploadFile(f)));
        fileContent = uploads.map((r) => r.data.extracted_text).join('\n\n');
      }

      const { data } = await chatApi.sendMessage(text, conversationId, fileContent);
      setConversationId(data.conversation_id);

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.reply,
        code: data.code ?? undefined,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
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
