/** Reusable Badge component. */
import React from "react";

type BadgeVariant = "success" | "warning" | "error" | "info" | "neutral";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = "neutral", className = "" }) => {
  const variantClasses = `badge badge-${variant}`;
  return <span className={`${variantClasses} ${className}`}>{children}</span>;
};