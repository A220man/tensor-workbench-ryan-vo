/** Tests for UI components. */
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { Button } from "../../ui/Button";
import { Badge } from "../../ui/Badge";
import { EmptyState } from "../../ui/EmptyState";
import { ErrorState } from "../../ui/ErrorState";

describe("Button", () => {
  it("renders with children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("btn-secondary");
  });

  it("applies size classes", () => {
    render(<Button size="sm">Small</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveClass("btn-sm");
  });

  it("shows loading spinner when loading", () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.getByRole("button")).toHaveClass("opacity-50");
  });

  it("calls onClick handler", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("Badge", () => {
  it("renders with children", () => {
    render(<Badge>Success</Badge>);
    expect(screen.getByText("Success")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success")).toHaveClass("badge-success");
  });

  it("applies error variant", () => {
    render(<Badge variant="error">Error</Badge>);
    expect(screen.getByText("Error")).toHaveClass("badge-error");
  });
});

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState title="No projects" description="Get started by scanning" />);
    expect(screen.getByText("No projects")).toBeInTheDocument();
    expect(screen.getByText("Get started by scanning")).toBeInTheDocument();
  });

  it("renders action button when provided", () => {
    const handleClick = vi.fn();
    render(
      <EmptyState
        title="Empty"
        action={{ label: "Scan", onClick: handleClick }}
      />
    );
    expect(screen.getByRole("button", { name: /scan/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /scan/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("ErrorState", () => {
  it("renders title and message", () => {
    render(<ErrorState title="Failed to load" message="Network error" />);
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    const handleRetry = vi.fn();
    render(<ErrorState title="Error" onRetry={handleRetry} retryLabel="Retry" />);
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});