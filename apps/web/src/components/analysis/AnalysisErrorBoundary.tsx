import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = { children: ReactNode };

type State = { error: Error | null };

/**
 * Prevents a single bad chart / 3D view / malformed replay payload from blanking the whole app.
 */
export class AnalysisErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Analysis render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="analysis-detail-page">
          <p className="status error" style={{ marginTop: 0 }}>
            This analysis could not be rendered safely:{" "}
            <code>{this.state.error.message}</code>
          </p>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            The run may still be valid on the server — try refreshing, or open
            an older analysis to compare. If this persists, the replay payload
            may contain an unexpected shape for one section.
          </p>
          <Link
            to="/dashboard"
            className="btn-primary"
            style={{ marginTop: "0.75rem" }}
          >
            Back to dashboard
          </Link>
        </div>
      );
    }
    return this.props.children;
  }
}
