/** Error state component. */
import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "./Button";

interface ErrorStateProps {
  title: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  onRetry,
  retryLabel = "Try again",
}) => {
  return (
    <div className="empty-state">
      <AlertCircle className="empty-state-icon text-error" size={64} />
      <h3 className="text-lg font-medium text-text mb-1">{title}</h3>
      {message && <p className="text-sm text-muted max-w-md">{message}</p>}
      {onRetry && (
        <Button variant="primary" size="sm" onClick={onRetry} className="mt-4 gap-2">
          <RefreshCw size={14} />
          {retryLabel}
        </Button>
      )}
    </div>
  );
};