/** Empty state component. */
import React from "react";
import { FolderOpen, RefreshCw, AlertCircle } from "lucide-react";
import { Button } from "./Button";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: "folder" | "refresh" | "alert";
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon = "folder",
  action,
}) => {
  const icons = {
    folder: <FolderOpen className="empty-state-icon" size={64} />,
    refresh: <RefreshCw className="empty-state-icon" size={64} />,
    alert: <AlertCircle className="empty-state-icon" size={64} />,
  };

  return (
    <div className="empty-state">
      {icons[icon]}
      <h3 className="text-lg font-medium text-text mb-1">{title}</h3>
      {description && <p className="text-sm text-muted max-w-md">{description}</p>}
      {action && (
        <Button variant="primary" size="sm" onClick={action.onClick} className="mt-4">
          {action.label}
        </Button>
      )}
    </div>
  );
};