import { useCallback, useEffect, useState } from "react";

/** 초 단위로 줄어드는 카운트다운. start(n)으로 시작하고 0이 되면 멈춘다. */
export function useCountdown() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = setTimeout(() => setSeconds((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [seconds]);

  const start = useCallback((n: number) => setSeconds(Math.max(0, Math.ceil(n))), []);
  return { seconds, start };
}
