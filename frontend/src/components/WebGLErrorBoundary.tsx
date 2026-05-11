"use client";

import React from "react";

interface State {
  hasError: boolean;
  message?: string;
}

export default class WebGLErrorBoundary extends React.Component<
  { children: React.ReactNode; label?: string },
  State
> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error) {
    // Swallow — the fallback UI handles it.
    if (process.env.NODE_ENV !== "production") {
      console.warn("[WebGLErrorBoundary]", error.message);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full w-full bg-surface border border-divider rounded-sm flex items-center justify-center text-center px-8">
          <div>
            <div className="smallcaps text-muted mb-2">
              {this.props.label ?? "Map"}
            </div>
            <p className="text-mono text-[11px] text-muted/80 max-w-[420px] leading-relaxed">
              WebGL unavailable on this device. The map renders as a static
              overview while the rest of the pipeline runs.
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
