import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Types for API responses
export interface AskRequest {
  question: string;
}

export interface AskResponse {
  answer: string;
  citations: string[];
  iterations?: SelfLoopIteration[];
  model_tier?: string;
  retrieval_mode?: string;
}

export interface SelfLoopIteration {
  step: 'plan' | 'draft' | 'critic' | 'verify' | 'revise';
  content: string;
  confidence?: number;
  timestamp: string;
}

export interface HealthResponse {
  ok: boolean;
}

export interface ReadyResponse {
  ready: boolean;
  services?: {
    qdrant?: boolean;
    elasticsearch?: boolean;
  };
}

export interface MetricsResponse {
  metrics: string; // Prometheus format
}

export interface TraceEntry {
  id: string;
  question: string;
  answer: string;
  model_tier: string;
  retrieval_mode: string;
  timestamp: string;
  latency_ms: number;
  status: 'success' | 'error';
}

export interface ApiConfig {
  baseURL: string;
  authToken?: string;
  timeout?: number;
}

class LiquidSquadAPI {
  private client: AxiosInstance;
  private authToken?: string;

  constructor(config: ApiConfig) {
    this.authToken = config.authToken;
    
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor
    this.client.interceptors.request.use((config) => {
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          console.error('Unauthorized: Invalid or missing auth token');
        } else if (error.response?.status === 429) {
          // Handle rate limiting
          console.error('Rate limit exceeded');
        }
        return Promise.reject(error);
      }
    );
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  async health(): Promise<HealthResponse> {
    const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
    return response.data;
  }

  async ready(): Promise<ReadyResponse> {
    const response: AxiosResponse<ReadyResponse> = await this.client.get('/ready');
    return response.data;
  }

  async ask(request: AskRequest): Promise<AskResponse> {
    const response: AxiosResponse<AskResponse> = await this.client.post('/ask', request);
    return response.data;
  }

  async metrics(): Promise<string> {
    const response: AxiosResponse<string> = await this.client.get('/metrics', {
      headers: {
        'Accept': 'text/plain',
      },
    });
    return response.data;
  }

  // Mock trace endpoint (would need to be implemented in FastAPI)
  async getTraces(page = 1, limit = 20, filter?: string): Promise<TraceEntry[]> {
    // This would be a real endpoint in production
    // For now, return mock data
    return [
      {
        id: '1',
        question: 'What is 2+2?',
        answer: '2+2 equals 4.',
        model_tier: 'small',
        retrieval_mode: 'disabled',
        timestamp: new Date().toISOString(),
        latency_ms: 150,
        status: 'success',
      },
      {
        id: '2',
        question: 'Explain quantum computing',
        answer: 'Quantum computing is a type of computation...',
        model_tier: 'large',
        retrieval_mode: 'dual',
        timestamp: new Date(Date.now() - 60000).toISOString(),
        latency_ms: 2500,
        status: 'success',
      },
    ];
  }
}

// Singleton instance
let apiInstance: LiquidSquadAPI | null = null;

export function createAPI(config: ApiConfig): LiquidSquadAPI {
  apiInstance = new LiquidSquadAPI(config);
  return apiInstance;
}

export function getAPI(): LiquidSquadAPI {
  if (!apiInstance) {
    throw new Error('API not initialized. Call createAPI first.');
  }
  return apiInstance;
}

// Utility function to parse Prometheus metrics
export function parsePrometheusMetrics(metricsText: string): Record<string, any> {
  const metrics: Record<string, any> = {};
  const lines = metricsText.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('#') || !line.trim()) continue;
    
    const match = line.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*(?:\{[^}]*\})?) (.+)$/);
    if (match) {
      const [, metricName, value] = match;
      const cleanName = metricName.split('{')[0];
      
      if (!metrics[cleanName]) {
        metrics[cleanName] = [];
      }
      
      metrics[cleanName].push({
        name: metricName,
        value: parseFloat(value),
      });
    }
  }
  
  return metrics;
}

export default LiquidSquadAPI;