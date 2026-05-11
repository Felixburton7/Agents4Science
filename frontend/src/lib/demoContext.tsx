"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Stage, STAGE_DURATIONS_MS, nextStage } from "@/lib/stages";
import { buildMockState, DEFAULT_HYPOTHESIS } from "@/lib/mockState";
import type { DemoState } from "@/types/schemas";

interface DemoContextValue {
  stage: Stage;
  state: DemoState;
  isRunning: boolean;
  hypothesis: string;
  setHypothesis: (s: string) => void;
  run: () => void;
  reset: () => void;
}

const Ctx = createContext<DemoContextValue | null>(null);

export function DemoProvider({ children }: { children: React.ReactNode }) {
  const [hypothesis, setHypothesis] = useState(DEFAULT_HYPOTHESIS);
  const [stage, setStage] = useState<Stage>(Stage.IDLE);
  const [state, setState] = useState<DemoState>(() => buildMockState(DEFAULT_HYPOTHESIS));
  const [isRunning, setIsRunning] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimer = () => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };

  const reset = useCallback(() => {
    clearTimer();
    setIsRunning(false);
    setStage(Stage.IDLE);
  }, []);

  const run = useCallback(() => {
    clearTimer();
    const fresh = buildMockState(hypothesis);
    setState(fresh);
    setStage(Stage.IDLE);
    setIsRunning(true);

    const advance = (current: Stage) => {
      const duration = STAGE_DURATIONS_MS[current];
      timer.current = setTimeout(() => {
        const next = nextStage(current);
        if (next === null) {
          setIsRunning(false);
          return;
        }
        setStage(next);
        if (next === Stage.DONE) {
          setIsRunning(false);
          return;
        }
        advance(next);
      }, duration);
    };

    setStage(Stage.PARSING);
    advance(Stage.PARSING);
  }, [hypothesis]);

  useEffect(() => () => clearTimer(), []);

  // ?autostart=1 query-string trigger — kicks off Run on mount. Useful for
  // headless-screenshot testing and for opening the demo "ready to go" on
  // stage day so the speaker only needs to point at the screen.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("autostart") === "1") {
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo(
    () => ({ stage, state, isRunning, hypothesis, setHypothesis, run, reset }),
    [stage, state, isRunning, hypothesis, run, reset],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useDemo() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useDemo must be used inside <DemoProvider />");
  return v;
}
