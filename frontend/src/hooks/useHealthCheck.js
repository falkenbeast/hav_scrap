import { useState, useEffect } from 'react';
import { api } from '../services/api';

/**
 * Custom React hook for monitoring backend service health status.
 */
export function useHealthCheck(pollIntervalMs = 30000) {
  const [health, setHealth] = useState({ status: 'checking', application: null });
  const [isHealthy, setIsHealthy] = useState(false);
  const [error, setError] = useState(null);

  const check = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
      setIsHealthy(data.status === 'healthy');
      setError(null);
    } catch (err) {
      setHealth({ status: 'unreachable' });
      setIsHealthy(false);
      setError(err.message || 'Backend connection failed');
    }
  };

  useEffect(() => {
    check();
    const interval = setInterval(check, pollIntervalMs);
    return () => clearInterval(interval);
  }, [pollIntervalMs]);

  return { health, isHealthy, error, checkNow: check };
}

