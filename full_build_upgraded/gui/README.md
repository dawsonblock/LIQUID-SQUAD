# LIQUID-SQUAD GUI

A production-grade Next.js frontend for the LIQUID-SQUAD AI Agent System.

## Features

- **Modern React Interface**: Built with Next.js 14, TypeScript, and TailwindCSS
- **Real-time Chat**: Interactive chat panel with self-loop iteration display
- **Metrics Dashboard**: Live monitoring with Chart.js visualizations
- **Trace Viewer**: Searchable and filterable request history
- **Responsive Design**: Mobile-first design with collapsible sidebar
- **Dark Mode**: System-aware theme switching
- **Authentication**: Bearer token support with local storage
- **Testing**: Comprehensive test suite with Jest and React Testing Library

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running LIQUID-SQUAD FastAPI backend

### Installation

1. **Install dependencies**:
   ```bash
   cd full_build_upgraded/gui
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your FastAPI backend URL
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Environment Variables

Create a `.env.local` file:

```bash
# FastAPI backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Default auth token (optional)
NEXT_PUBLIC_DEFAULT_AUTH_TOKEN=your-secret-token-here

# App configuration
NEXT_PUBLIC_APP_NAME=LIQUID-SQUAD
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run test` - Run test suite
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report

## Architecture

### Pages

- **`/`** - Main chat interface
- **`/metrics`** - Real-time metrics dashboard
- **`/settings`** - Configuration and trace viewer

### Components

- **`ChatPanel`** - Main chat interface with message history
- **`Sidebar`** - Navigation and operator controls
- **`Layout`** - Responsive layout wrapper
- **`IterationCard`** - Self-loop iteration display
- **`MetricsChart`** - Chart.js wrapper for metrics
- **`TraceTable`** - Searchable trace history

### API Integration

- **`lib/api.ts`** - FastAPI client with TypeScript types
- **`pages/api/proxy/[...path].ts`** - CORS proxy for backend calls

## Features in Detail

### Chat Interface

- Multiline question input with keyboard shortcuts
- Real-time self-loop iteration display
- Citation rendering with expandable previews
- Markdown support for math (KaTeX) and code (Prism.js)
- Message history with timestamps

### Metrics Dashboard

- Request volume over time (line chart)
- Response latency distribution (bar chart)
- Status code breakdown (doughnut chart)
- Model tier usage (doughnut chart)
- Auto-refresh every 10 seconds
- Summary cards with key metrics

### Settings & Configuration

- API endpoint configuration
- Authentication token management
- Theme selection (light/dark/system)
- Auto-refresh settings
- Connection status monitoring

### Trace Viewer

- Searchable request history
- Filter by status (success/error)
- Pagination with configurable page size
- Detailed trace inspection modal
- Export capabilities (future enhancement)

## Mobile Responsiveness

The interface is fully responsive with:

- Collapsible sidebar on mobile devices
- Touch-friendly controls and buttons
- Optimized layouts for different screen sizes
- Swipe gestures for navigation (future enhancement)

## Testing

Run the test suite:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

Test files are located in `__tests__/` and cover:

- Component rendering and interactions
- API client functionality
- Utility functions
- Integration scenarios

## Deployment

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
npm run start
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

Build and run:

```bash
docker build -t liquid-squad-gui .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your-api:8000 liquid-squad-gui
```

## Customization

### Styling

- Modify `tailwind.config.js` for theme customization
- Update `styles/globals.css` for global styles
- Component-specific styles use Tailwind classes

### API Integration

- Extend `lib/api.ts` for new endpoints
- Add types in the same file for TypeScript support
- Update proxy configuration in `next.config.js` if needed

### Charts and Metrics

- Customize charts in `components/MetricsChart.tsx`
- Add new metric types in `pages/metrics.tsx`
- Extend Prometheus parsing in `lib/api.ts`

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Code splitting with Next.js dynamic imports
- Image optimization with Next.js Image component
- Bundle analysis with `@next/bundle-analyzer`
- Lazy loading for non-critical components

## Security

- CSP headers configured in `next.config.js`
- XSS protection with React's built-in sanitization
- Secure token storage in localStorage
- HTTPS enforcement in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

See the main project LICENSE file for details.

## Support

For issues and questions:

1. Check the [main project documentation](../README.md)
2. Review the [API documentation](../full_build/README.md)
3. Open an issue on GitHub
4. Contact the development team

---

Built with ❤️ using Next.js, TypeScript, and TailwindCSS.