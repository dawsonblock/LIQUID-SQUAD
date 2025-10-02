import { render, screen } from '@testing-library/react';
import Sidebar from '@/components/Sidebar';

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({
    pathname: '/',
  }),
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  MessageSquare: () => <div data-testid="message-square-icon" />,
  BarChart3: () => <div data-testid="bar-chart-icon" />,
  Settings: () => <div data-testid="settings-icon" />,
  Menu: () => <div data-testid="menu-icon" />,
  X: () => <div data-testid="x-icon" />,
  Bot: () => <div data-testid="bot-icon" />,
  Database: () => <div data-testid="database-icon" />,
  Shield: () => <div data-testid="shield-icon" />,
  ExternalLink: () => <div data-testid="external-link-icon" />,
  Moon: () => <div data-testid="moon-icon" />,
  Sun: () => <div data-testid="sun-icon" />,
}));

describe('Sidebar', () => {
  const defaultProps = {
    isOpen: true,
    onToggle: jest.fn(),
    modelTier: 'auto',
    onModelTierChange: jest.fn(),
    retrievalMode: 'disabled',
    onRetrievalModeChange: jest.fn(),
    criticEnabled: true,
    onCriticToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders sidebar with navigation items', () => {
    render(<Sidebar {...defaultProps} />);
    
    expect(screen.getByText('LIQUID-SQUAD')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Metrics')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders control sections', () => {
    render(<Sidebar {...defaultProps} />);
    
    expect(screen.getByText('Auth Token')).toBeInTheDocument();
    expect(screen.getByText('Model Tier')).toBeInTheDocument();
    expect(screen.getByText('Retrieval Mode')).toBeInTheDocument();
    expect(screen.getByText('Enable Critic')).toBeInTheDocument();
  });

  it('shows correct model tier selection', () => {
    render(<Sidebar {...defaultProps} modelTier="large" />);
    
    const modelSelect = screen.getByDisplayValue('Large');
    expect(modelSelect).toBeInTheDocument();
  });

  it('shows correct retrieval mode selection', () => {
    render(<Sidebar {...defaultProps} retrievalMode="dual" />);
    
    const retrievalSelect = screen.getByDisplayValue('Dual');
    expect(retrievalSelect).toBeInTheDocument();
  });

  it('shows critic checkbox as checked when enabled', () => {
    render(<Sidebar {...defaultProps} criticEnabled={true} />);
    
    const criticCheckbox = screen.getByRole('checkbox');
    expect(criticCheckbox).toBeChecked();
  });

  it('shows critic checkbox as unchecked when disabled', () => {
    render(<Sidebar {...defaultProps} criticEnabled={false} />);
    
    const criticCheckbox = screen.getByRole('checkbox');
    expect(criticCheckbox).not.toBeChecked();
  });
});