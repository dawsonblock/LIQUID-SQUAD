
# LIQUID HIVE 25 Frontend

Modern, responsive frontend for the LIQUID HIVE 25 multi-tier LLM system.

## Features

- 🎨 Modern UI with Tailwind CSS
- 💬 Real-time chat interface
- 📝 Markdown rendering with syntax highlighting
- 🔐 JWT authentication
- 💾 Conversation management
- 📱 Responsive design
- ⚡ Fast and optimized with Next.js 14

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
npm install
# or
yarn install
```

### Development

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

### Build

```bash
npm run build
npm start
# or
yarn build
yarn start
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   ├── pages/          # Next.js pages
│   ├── lib/            # Utilities and API client
│   ├── hooks/          # Custom React hooks
│   └── styles/         # Global styles
├── public/             # Static assets
└── package.json
```

## Technologies

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **Lucide React** - Icons
