import { 
  cn, 
  formatTimestamp, 
  formatDuration, 
  truncateText,
  getStoredAuthToken,
  setStoredAuthToken,
  removeStoredAuthToken
} from '@/lib/utils';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Utils Library', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('cn', () => {
    it('merges class names correctly', () => {
      const result = cn('base-class', 'additional-class');
      expect(result).toContain('base-class');
      expect(result).toContain('additional-class');
    });

    it('handles conditional classes', () => {
      const result = cn('base-class', true && 'conditional-class', false && 'hidden-class');
      expect(result).toContain('base-class');
      expect(result).toContain('conditional-class');
      expect(result).not.toContain('hidden-class');
    });
  });

  describe('formatTimestamp', () => {
    it('formats timestamp correctly', () => {
      const timestamp = '2023-12-01T12:00:00Z';
      const result = formatTimestamp(timestamp);
      expect(result).toBeDefined();
      expect(typeof result).toBe('string');
    });
  });

  describe('formatDuration', () => {
    it('formats milliseconds correctly', () => {
      expect(formatDuration(500)).toBe('500ms');
      expect(formatDuration(1500)).toBe('1.5s');
      expect(formatDuration(65000)).toBe('1.1m');
    });
  });

  describe('truncateText', () => {
    it('truncates long text', () => {
      const longText = 'This is a very long text that should be truncated';
      const result = truncateText(longText, 20);
      expect(result).toBe('This is a very long ...');
      expect(result.length).toBe(23); // 20 + '...'
    });

    it('returns original text if shorter than max length', () => {
      const shortText = 'Short text';
      const result = truncateText(shortText, 20);
      expect(result).toBe(shortText);
    });
  });

  describe('localStorage functions', () => {
    it('gets stored auth token', () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      const result = getStoredAuthToken();
      expect(result).toBe('test-token');
      expect(localStorageMock.getItem).toHaveBeenCalledWith('liquid-squad-auth-token');
    });

    it('sets stored auth token', () => {
      setStoredAuthToken('new-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('liquid-squad-auth-token', 'new-token');
    });

    it('removes stored auth token', () => {
      removeStoredAuthToken();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('liquid-squad-auth-token');
    });
  });
});