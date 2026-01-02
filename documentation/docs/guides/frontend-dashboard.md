# Frontend Dashboard

SolanaLM includes a modern web dashboard built with Vue.js for monitoring and managing nodes.

## Overview

The frontend dashboard provides a rich graphical interface for:

- Real-time node monitoring
- Network statistics and metrics
- Training round visualization
- Earnings tracking and charts
- Node management

## Quick Start

### Development Server

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Vue.js | 3.4+ | Reactive UI framework |
| Vite | 5.0+ | Build tool and dev server |
| Tailwind CSS | 3.4+ | Utility-first styling |
| Pinia | 2.1+ | State management |
| Vue Router | 4.2+ | Client-side routing |
| Chart.js | 4.4+ | Data visualization |
| Axios | 1.6+ | HTTP client |

## Project Structure

```
frontend/
├── src/
│   ├── App.vue           # Root component
│   ├── main.ts           # Application entry
│   ├── router/           # Route definitions
│   ├── views/            # Page components
│   ├── components/       # Reusable components
│   ├── stores/           # Pinia state stores
│   ├── services/         # API services
│   └── assets/           # Static assets
├── package.json          # Dependencies
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
└── tsconfig.json         # TypeScript config
```

## Features

### Dashboard View

The main dashboard displays:

- Node health status indicators
- Real-time request metrics
- Network connectivity status
- Resource utilization graphs
- Recent activity feed

### Nodes View

Manage and monitor all connected nodes:

- Node list with status
- Individual node details
- Performance metrics
- Configuration options

### Training View

Monitor federated learning activities:

- Active training rounds
- Participation metrics
- Model convergence graphs
- Privacy budget tracking

### Earnings View

Track SOL earnings:

- Earnings summary cards
- Historical charts
- Payment history table
- Projected earnings

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws

# Feature Flags
VITE_ENABLE_TRAINING_VIEW=true
VITE_ENABLE_EARNINGS_VIEW=true
```

### API Connection

Configure the gateway URL in the services:

```typescript
// src/services/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  timeout: 30000,
})

export default api
```

## Development

### Running Locally

```bash
# Start gateway (required for API)
python scripts/run_gateway.py

# Start frontend dev server
cd frontend && npm run dev
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Building for Production

### Standalone Build

```bash
npm run build
# Output in dist/
```

### Docker Build

```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Integration with Gateway

The frontend can be served by the gateway for single-deployment:

```python
# In gateway configuration
STATIC_FILES_PATH = "./frontend/dist"
```

## Customization

### Theming

Customize colors in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f5f3ff',
          500: '#8b5cf6',
          900: '#4c1d95',
        },
        // Add custom colors
      },
    },
  },
}
```

### Adding Pages

1. Create a new view in `src/views/`:

```vue
<!-- src/views/NewView.vue -->
<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">New Page</h1>
  </div>
</template>
```

2. Add route in `src/router/index.ts`:

```typescript
{
  path: '/new-page',
  name: 'NewPage',
  component: () => import('@/views/NewView.vue')
}
```

### Adding Components

Create reusable components in `src/components/`:

```vue
<!-- src/components/StatusBadge.vue -->
<template>
  <span :class="badgeClass">{{ status }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: 'online' | 'offline' | 'busy'
}>()

const badgeClass = computed(() => ({
  'bg-green-500': props.status === 'online',
  'bg-red-500': props.status === 'offline',
  'bg-yellow-500': props.status === 'busy',
}))
</script>
```

## WebSocket Integration

Real-time updates via WebSocket:

```typescript
// src/services/websocket.ts
import { ref } from 'vue'

const ws = ref<WebSocket | null>(null)

export function useWebSocket(url: string) {
  ws.value = new WebSocket(url)

  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // Handle updates
  }

  return { ws }
}
```

## Troubleshooting

### CORS Issues

Ensure the gateway allows frontend origin:

```python
# Gateway configuration
CORS_ORIGINS = ["http://localhost:5173"]
```

### Build Errors

Clear cache and reinstall:

```bash
rm -rf node_modules
rm package-lock.json
npm install
```

### API Connection Failed

Check gateway is running and URL is correct:

```bash
curl http://localhost:8001/health
```

## Next Steps

- [Gateway API](../api/gateway.md) - API reference
- [TUI Guide](tui.md) - Terminal interface alternative
- [Docker Deployment](../deployment/docker.md) - Container deployment
