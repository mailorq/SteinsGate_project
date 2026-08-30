import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

interface AppErrorBoundaryProps {
  children: ReactNode;
}

interface AppErrorBoundaryState {
  hasError: boolean;
}

export class AppErrorBoundary extends Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error("Unhandled application error", error, errorInfo.componentStack);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="flex min-h-screen items-center justify-center px-4 py-12 text-zinc-100">
          <section
            className="w-full max-w-md rounded-2xl border border-zinc-800/80 bg-zinc-950/60 p-8 text-center shadow-2xl shadow-black/40 backdrop-blur-sm md:p-10"
            role="alert"
            aria-labelledby="application-error-title"
          >
            <p className="font-mono text-xs tracking-[0.2em] text-amber-400 uppercase">System Error</p>
            <h1 id="application-error-title" className="mt-3 text-2xl font-semibold tracking-tight">
              Что-то пошло не так
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">
              Страница столкнулась с непредвиденной ошибкой. Перезагрузите её и попробуйте снова.
            </p>
            <button
              type="button"
              className="mt-7 inline-flex min-h-11 cursor-pointer items-center justify-center rounded-lg border border-amber-500/40 bg-amber-500/10 px-5 text-sm font-medium text-amber-300 transition-colors hover:bg-amber-500/20 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-400"
              onClick={() => window.location.reload()}
            >
              Перезагрузить страницу
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
