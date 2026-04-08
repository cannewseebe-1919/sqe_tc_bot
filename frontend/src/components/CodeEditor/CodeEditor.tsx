import Editor from '@monaco-editor/react';
import './CodeEditor.css';

interface Props {
  code: string;
  onChange: (code: string) => void;
  readOnly?: boolean;
}

export default function CodeEditor({ code, onChange, readOnly }: Props) {
  return (
    <div className="code-editor-panel">
      <div className="code-editor-header">
        <span>TC 코드 에디터</span>
        <span className="code-lang">Python</span>
      </div>
      <div className="code-editor-body">
        <Editor
          height="100%"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(v) => onChange(v ?? '')}
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            automaticLayout: true,
            tabSize: 4,
          }}
        />
      </div>
    </div>
  );
}
