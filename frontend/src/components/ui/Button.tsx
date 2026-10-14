/** Reusable Button component. */
import React from "react";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "default" | "sm";
  loading?: boolean;
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "default", loading, disabled, children, className = "", ...props }, ref) => {
    const baseClasses = "btn";
    const variantClasses = `btn-${variant}`;
    const sizeClasses = size === "sm" ? "btn-sm" : "";
    const loadingClasses = loading ? "opacity-50 cursor-wait" : "";

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${baseClasses} ${variantClasses} ${sizeClasses} ${loadingClasses} ${className}`}
        {...props}
      >
        {loading && <Loader2 className="spinner" size={16} />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";