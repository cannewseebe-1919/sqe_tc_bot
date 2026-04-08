import { useState, useRef, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import type { FileAttachment } from '../../services/types';
import './Chat.css';

interface Props {
  onSend: (message: string, files: File[]) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const onDrop = useCallback((accepted: File[]) => {
    const valid = accepted.filter(
      (f) =>
        f.name.endsWith('.docx') ||
        f.name.endsWith('.pdf')
    );
    setFiles((prev) => [...prev, ...valid]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    noClick: true,
    noKeyboard: true,
  });

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed && files.length === 0) return;
    onSend(trimmed, files);
    setText('');
    setFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  return (
    <div className="chat-input-area" {...getRootProps()}>
      <input {...getInputProps()} />
      {isDragActive && (
        <div className="drop-overlay">Word(.docx) 또는 PDF 파일을 놓으세요</div>
      )}
      {files.length > 0 && (
        <div className="attached-files">
          {files.map((f, i) => (
            <span key={i} className="file-chip">
              {f.name}
              <button onClick={() => removeFile(i)}>&times;</button>
            </span>
          ))}
        </div>
      )}
      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="테스트 케이스를 설명해 주세요..."
          rows={1}
          disabled={disabled}
        />
        <button
          className="send-btn"
          onClick={handleSubmit}
          disabled={disabled || (!text.trim() && files.length === 0)}
        >
          전송
        </button>
      </div>
    </div>
  );
}
