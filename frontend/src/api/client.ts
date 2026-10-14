/** Typed API client using axios. */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import type {
  Project,
  ProjectListResponse,
  ScanResponse,
  HealthResponse,
  VersionResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add auth token if available (for future OIDC integration)
        const token = localStorage.getItem("access_token");
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Clear token and redirect to login (future)
          localStorage.removeItem("access_token");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  /** Health check */
  async health(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>("/health");
    return data;
  }

  /** Get version info */
  async version(): Promise<VersionResponse> {
    const { data } = await this.client.get<VersionResponse>("/version");
    return data;
  }

  /** List projects with pagination and filtering */
  async listProjects(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<ProjectListResponse> {
    const { data } = await this.client.get<ProjectListResponse>("/projects", { params });
    return data;
  }

  /** Get a single project by ID */
  async getProject(id: number): Promise<Project> {
    const { data } = await this.client.get<Project>(`/projects/${id}`);
    return data;
  }

  /** Trigger workspace scan */
  async scanWorkspace(): Promise<ScanResponse> {
    const { data } = await this.client.post<ScanResponse>("/projects/scan");
    return data;
  }
}

export const api = new ApiClient();