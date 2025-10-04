import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatPanel from '@/components/ChatPanel';
import { AskRequest, AskResponse, SelfLoopIteration } from '@/lib/api';

const mockSuccess = jest.fn();
const mockError = jest.fn();

jest.mock('react-hot-toast', () => ({
  toast: {
    success: (msg: string) => mockSuccess(msg),
    error: (msg: string) => mockError(msg),
  },
}));

jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/',
    push: jest.fn(),
  }),
}));

describe('ChatPanel', () => {
  const mockOnSubmit = jest.fn<Promise<AskResponse>, [AskRequest, { onIteration: (iteration: SelfLoopIteration) => void }]>();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders welcome message when no messages', () => {
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);

    expect(screen.getByText('Welcome to LIQUID-SQUAD')).toBeInTheDocument();
    expect(screen.getByText(/Ask me anything!/)).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('shows loading spinner on send button when loading', () => {
    const { container } = render(<ChatPanel onSubmit={mockOnSubmit} isLoading={true} />);

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
    expect(container.querySelector('svg.animate-spin')).toBeInTheDocument();
  });

  it('streams iterations and renders final answer', async () => {
    const iteration: SelfLoopIteration = {
      step: 'plan',
      content: '- Outline the response',
      timestamp: '2024-01-01T00:00:00Z',
      confidence: 0.5,
      round: 1,
    };

    const response: AskResponse = {
      answer: 'Final answer',
      citations: [],
      iterations: [iteration],
      model_tier: 'small',
      retrieval_mode: 'disabled',
      duration_ms: 1200,
      rounds: 1,
    };

    mockOnSubmit.mockImplementation(async (_request, handlers) => {
      handlers.onIteration(iteration);
      return response;
    });

    const { container } = render(<ChatPanel onSubmit={mockOnSubmit} isLoading={false} />);

    const textarea = screen.getByPlaceholderText('Ask me anything...');
    fireEvent.change(textarea, { target: { value: 'Hello world' } });

    const form = container.querySelector('form');
    expect(form).not.toBeNull();
    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        { question: 'Hello world' },
        expect.objectContaining({ onIteration: expect.any(Function) })
      );
    });

    await screen.findByText('Self-Loop Process');
    await screen.findByText('Final answer');
  });
});
