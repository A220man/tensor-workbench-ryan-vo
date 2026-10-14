/** Loading spinner component. */
import React from "react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = "md", className = "" }) => {
  const sizeClasses = {
    sm: "w-4 h-4 border-[1.5px]",
    md: "w-5 h-5 border-2",
    lg: "w-8 h-8 border-2",
  };

  return (
    <div
      className={`${sizeClasses[size]} border-border-light border-t-primary rounded-full animate-spin ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
};