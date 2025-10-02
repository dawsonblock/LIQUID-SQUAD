import { createAPI, parsePrometheusMetrics } from '@/lib/api';

describe('API Library', () => {
  describe('createAPI', () => {
    it('creates API instance with correct config', () => {
      const config = {
        baseURL: 'http://localhost:8000',
        authToken: 'test-token',
        timeout: 5000,
      };
      
      const api = createAPI(config);
      expect(api).toBeDefined();
    });
  });

  describe('parsePrometheusMetrics', () => {
    it('parses simple metrics correctly', () => {
      const metricsText = `
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1234
http_requests_total{method="POST",status="201"} 567
http_request_duration_seconds 0.123
`;
      
      const parsed = parsePrometheusMetrics(metricsText);
      
      expect(parsed).toHaveProperty('http_requests_total');
      expect(parsed).toHaveProperty('http_request_duration_seconds');
      expect(parsed.http_requests_total).toHaveLength(2);
      expect(parsed.http_request_duration_seconds).toHaveLength(1);
    });

    it('handles empty metrics text', () => {
      const parsed = parsePrometheusMetrics('');
      expect(parsed).toEqual({});
    });

    it('ignores comments and empty lines', () => {
      const metricsText = `
# This is a comment
# Another comment

metric_name 42

# More comments
`;
      
      const parsed = parsePrometheusMetrics(metricsText);
      expect(parsed).toHaveProperty('metric_name');
      expect(parsed.metric_name).toHaveLength(1);
      expect(parsed.metric_name[0].value).toBe(42);
    });
  });
});