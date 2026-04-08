import { useState, useEffect } from 'react';
import { deviceApi } from '../../services/api';
import type { Device } from '../../services/types';
import './DeviceSelector.css';

interface Props {
  selectedId: string | null;
  onSelect: (device: Device) => void;
}

const STATUS_LABELS: Record<Device['status'], string> = {
  CONNECTED: '대기중',
  TESTING: '테스트중',
  QUEUED: '대기열',
  OFFLINE: '오프라인',
  ERROR: '오류',
};

const STATUS_COLORS: Record<Device['status'], string> = {
  CONNECTED: '#43a047',
  TESTING: '#fb8c00',
  QUEUED: '#fdd835',
  OFFLINE: '#9e9e9e',
  ERROR: '#e53935',
};

export default function DeviceSelector({ selectedId, onSelect }: Props) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDevices = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await deviceApi.list();
      setDevices(data.devices);
    } catch {
      setError('단말 목록을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  return (
    <div className="device-selector">
      <div className="device-selector-header">
        <span>단말 선택</span>
        <button className="refresh-btn" onClick={fetchDevices} disabled={loading}>
          {loading ? '...' : '새로고침'}
        </button>
      </div>
      {error && <div className="device-error">{error}</div>}
      <div className="device-list">
        {devices.length === 0 && !loading && !error && (
          <div className="device-empty">연결된 단말이 없습니다.</div>
        )}
        {devices.map((d) => (
          <div
            key={d.id}
            className={`device-card ${selectedId === d.id ? 'selected' : ''} ${
              d.status !== 'CONNECTED' ? 'unavailable' : ''
            }`}
            onClick={() => d.status === 'CONNECTED' && onSelect(d)}
          >
            <div className="device-card-top">
              <span
                className="status-dot"
                style={{ background: STATUS_COLORS[d.status] }}
              />
              <span className="device-name">{d.name}</span>
            </div>
            <div className="device-card-info">
              <span>{d.model}</span>
              <span>Android {d.android_version}</span>
              <span className="device-status-label">
                {STATUS_LABELS[d.status]}
              </span>
            </div>
            {d.queue_length > 0 && (
              <div className="device-queue">대기: {d.queue_length}건</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
