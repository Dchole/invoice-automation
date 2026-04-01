import { useState, useCallback } from 'react';

/**
 * Hook for async actions with loading state and error handling.
 * Returns { run, loading, error } where run() wraps the async fn
 * with loading tracking, error catching, and optional callbacks.
 */
export function useAction(asyncFn, { onSuccess, onError } = {}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await asyncFn(...args);
      onSuccess?.(result);
      return result;
    } catch (e) {
      const msg = e.message || 'Something went wrong';
      setError(msg);
      onError?.(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [asyncFn, onSuccess, onError]);

  return { run, loading, error };
}
