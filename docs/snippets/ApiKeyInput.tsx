import { useState, useEffect } from 'react';

const STORAGE_KEY = 'skillet_anthropic_api_key';

interface ApiKeyInputProps {
  onKeyChange: (key: string | null) => void;
}

/**
 * BYOK (Bring Your Own Key) API key input component.
 * Stores key in localStorage - never sent to our servers.
 */
export function ApiKeyInput({ onKeyChange }: ApiKeyInputProps) {
  const [apiKey, setApiKey] = useState<string>('');
  const [isStored, setIsStored] = useState(false);
  const [showKey, setShowKey] = useState(false);

  // Load stored key on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setApiKey(stored);
      setIsStored(true);
      onKeyChange(stored);
    }
  }, [onKeyChange]);

  const handleSave = () => {
    if (apiKey.trim()) {
      localStorage.setItem(STORAGE_KEY, apiKey.trim());
      setIsStored(true);
      onKeyChange(apiKey.trim());
    }
  };

  const handleClear = () => {
    localStorage.removeItem(STORAGE_KEY);
    setApiKey('');
    setIsStored(false);
    onKeyChange(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    }
  };

  return (
    <div style={{
      padding: '12px 16px',
      background: '#f8f9fa',
      borderRadius: '8px',
      marginBottom: '12px',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '8px',
      }}>
        <span style={{ fontSize: '14px', fontWeight: 500 }}>
          Anthropic API Key
        </span>
        {isStored && (
          <span style={{
            fontSize: '11px',
            padding: '2px 6px',
            background: '#dcfce7',
            color: '#166534',
            borderRadius: '4px',
          }}>
            Saved locally
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type={showKey ? 'text' : 'password'}
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="sk-ant-..."
          style={{
            flex: 1,
            padding: '8px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px',
            fontFamily: 'monospace',
          }}
        />
        <button
          onClick={() => setShowKey(!showKey)}
          style={{
            padding: '8px 12px',
            background: 'white',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          {showKey ? 'Hide' : 'Show'}
        </button>
        {!isStored ? (
          <button
            onClick={handleSave}
            disabled={!apiKey.trim()}
            style={{
              padding: '8px 16px',
              background: apiKey.trim() ? '#3b82f6' : '#9ca3af',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: apiKey.trim() ? 'pointer' : 'not-allowed',
              fontSize: '14px',
            }}
          >
            Save
          </button>
        ) : (
          <button
            onClick={handleClear}
            style={{
              padding: '8px 16px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Clear
          </button>
        )}
      </div>

      <p style={{
        fontSize: '12px',
        color: '#6b7280',
        marginTop: '8px',
        marginBottom: 0,
      }}>
        Your key is stored locally in your browser and never sent to our servers.
        Get your key from{' '}
        <a
          href="https://console.anthropic.com/"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#3b82f6' }}
        >
          console.anthropic.com
        </a>
      </p>
    </div>
  );
}

export default ApiKeyInput;
