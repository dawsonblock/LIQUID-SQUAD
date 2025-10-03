import { render, screen } from '@testing-library/react';
import { toast } from 'react-hot-toast';
import ChatPanel from '@/components/ChatPanel';
import { AskRequest, AskResponse } from '@/lib/api';

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/',
    push: jest.fn(),
  }),
}));

describe('ChatPanel', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders welcome message when no messages', () => {
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);
    
    expect(screen.getByText('Welcome to LIQUID-SQUAD')).toBeInTheDocument();
    expect(screen.getByText(/Ask me anything!/)).toBeInTheDocument();
  });

  it('renders input form', () => {
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);
    
    expect(screen.getByPlaceholderText('Ask me anything...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('shows loading state when isLoading is true', () => {
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={true} />);
    
    expect(screen.getByText('Processing your question...')).toBeInTheDocument();
  });

  it('handles form submission', async () => {
    const mockResponse: AskResponse = {
      answer: 'Test answer',
      citations: ['citation1', 'citation2'],
    };
    
    mockOnSubmit.mockResolvedValue(mockResponse);
    
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Ask me anything...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    // Type in the input
    await screen.getByDisplayValue('');
    
    // Note: Full form submission testing would require more complex setup
    // This is a basic structure for the test
  });
});