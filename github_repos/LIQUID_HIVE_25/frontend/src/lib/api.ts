
import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  loadToken() {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        this.token = token;
      }
    }
  }

  async ask(question: string): Promise<{ answer: string }> {
    const response = await this.client.post('/ask', { question });
    return response.data;
  }

  async health(): Promise<{ status: string; timestamp: number }> {
    const response = await this.client.get('/healthz');
    return response.data;
  }

  async ready(): Promise<{ status: string; timestamp: number }> {
    const response = await this.client.get('/readyz');
    return response.data;
  }

  async createToken(userId: string, expiresHours?: number): Promise<{ token: string }> {
    const response = await this.client.post('/auth/token', {
      user_id: userId,
      expires_hours: expiresHours,
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
