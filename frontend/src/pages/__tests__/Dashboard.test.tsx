/** Tests for Dashboard page. */
import { render, screen, waitFor, act, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { vi } from "vitest";
import { Dashboard } from "../../pages/Dashboard";

// Mock the API
vi.mock("../../api", () => ({
  api: {
    listProjects: vi.fn(),
    scanWorkspace: vi.fn(),
  },
  type: {},
}));

import { api } from "../../api";

const mockProjects = [
  {
    id: 1,
    name: "TestApp",
    path: "/workspace/TestApp",
    package_name: "TestApp",
    package_version: "1.0.0",
    swift_tools_version: "5.9",
    status: "valid" as const,
    description: "A test app",
    targets: ["TestApp", "TestAppTests"],
    dependencies: ["https://github.com/apple/swift-argument-parser"],
    latest_build: {
      id: 1,
      target: "device" as const,
      configuration: "debug",
      status: "success" as const,
      started_at: "2024-01-01T00:00:00Z",
      completed_at: "2024-01-01T00:01:00Z",
      duration_seconds: 60,
    },
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "InvalidApp",
    path: "/workspace/InvalidApp",
    package_name: "InvalidApp",
    package_version: "0.1.0",
    swift_tools_version: "5.8",
    status: "invalid" as const,
    description: null,
    targets: [],
    dependencies: [],
    latest_build: undefined,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

function renderDashboard() {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    (api.listProjects as vi.Mock).mockImplementation(() => new Promise(() => {})); // never resolves
    renderDashboard();
    expect(screen.getByRole("status")).toBeInTheDocument(); // LoadingSpinner has role=status
  });

  it("renders projects table when data loads", async () => {
    (api.listProjects as vi.Mock).mockResolvedValue({
      projects: mockProjects,
      total: 2,
      limit: 20,
      offset: 0,
    });

    renderDashboard();

    await waitFor(() => {
      // Use getAllByText to find all occurrences, then check at least one exists
      expect(screen.getAllByText("TestApp").length).toBeGreaterThan(0);
      expect(screen.getAllByText("InvalidApp").length).toBeGreaterThan(0);
    });
  });

  it("shows empty state when no projects", async () => {
    (api.listProjects as vi.Mock).mockResolvedValue({
      projects: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("No projects found")).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    (api.listProjects as vi.Mock).mockRejectedValue(new Error("Network error"));

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });
  it("calls scanWorkspace when Scan button clicked", async () => {
    (api.listProjects as vi.Mock).mockResolvedValue({
      projects: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    (api.scanWorkspace as vi.Mock).mockResolvedValue({
      scanned: 1,
      added: 1,
      updated: 0,
      errors: [],
    });

    renderDashboard();

    // Wait for loading to finish (button to be enabled)
    await waitFor(() => {
      const buttons = screen.getAllByRole("button", { name: /scan workspace/i });
      expect(buttons.length).toBeGreaterThanOrEqual(1);
      // First button should be the header one (not disabled)
      expect(buttons[0]).not.toBeDisabled();
    });

    // Click the header Scan Workspace button
    await act(async () => {
      const buttons = screen.getAllByRole("button", { name: /scan workspace/i });
      fireEvent.click(buttons[0]);
    });

    // Wait for scanWorkspace to be called
    await waitFor(() => {
      expect(api.scanWorkspace).toHaveBeenCalledTimes(1);
    });
  });

  it("displays project status badges correctly", async () => {
    (api.listProjects as vi.Mock).mockResolvedValue({
      projects: mockProjects,
      total: 2,
      limit: 20,
      offset: 0,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Valid")).toBeInTheDocument();
      expect(screen.getByText("Invalid")).toBeInTheDocument();
    });
  });

  it("displays build status for projects with builds", async () => {
    (api.listProjects as vi.Mock).mockResolvedValue({
      projects: mockProjects,
      total: 2,
      limit: 20,
      offset: 0,
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Success")).toBeInTheDocument();
    });
  });
});