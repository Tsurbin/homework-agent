# Homework Agent - React Client

A modern React web application built with TypeScript, Vite, and Tailwind CSS for viewing and managing homework assignments. This frontend provides an intuitive interface to query homework data stored in DynamoDB and scraped by the Node.js scraper.

## 🎯 Purpose

This client application:
- Displays homework assignments in a user-friendly interface
- Shows weekly class schedules and plans
- Allows filtering and searching homework by subject, date, status
- Provides a responsive design for mobile and desktop
- Integrates with the node-server API for data access

## 🏗️ Tech Stack

- **React 19**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **ESLint**: Code linting and quality checks

## 🚀 Quick Start

### Prerequisites

- Node.js 20.x or later
- npm or yarn

### Installation

```bash
cd client
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

Build output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 📦 Deployment

### Deploy to AWS S3 + CloudFront

The application can be deployed to AWS using S3 for hosting and CloudFront for CDN:

```bash
npm run deploy
```

This script:
1. Builds the production bundle
2. Creates/updates CloudFormation stack
3. Uploads files to S3 bucket
4. Configures CloudFront distribution
5. Outputs the CloudFront URL

The deployment is configured in:
- `deploy-s3-cloudfront.sh`: Deployment script
- `cloudformation-s3-cloudfront.yaml`: Infrastructure template

### Manual Deployment

```bash
# Build the app
npm run build

# Deploy to your hosting provider
# Upload contents of dist/ directory
```

## 📂 Project Structure

```
client/
├── src/
│   ├── components/          # React components
│   │   └── ...
│   ├── App.tsx              # Main App component
│   ├── App.css              # App styles
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles (Tailwind)
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── eslint.config.js         # ESLint configuration
├── package.json
├── deploy-s3-cloudfront.sh
├── cloudformation-s3-cloudfront.yaml
└── README.md
```

## 🎨 Features

### Current Features
- Modern, responsive UI
- Fast development with Vite HMR
- Type-safe with TypeScript
- Styled with Tailwind CSS

### Planned Features
- Homework list view with filtering
- Weekly schedule calendar view
- Search and filter by subject, date
- Status management (pending, completed)
- Dark mode support
- Notifications for upcoming homework

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `client` directory:

```bash
# API Backend URL
VITE_API_URL=http://localhost:8000

# Optional: Feature flags
VITE_ENABLE_DARK_MODE=true
```

### API Integration

The client communicates with the node-server API:

```typescript
// Example API call
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchHomework() {
  const response = await fetch(`${API_URL}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'Get all homework' })
  });
  return response.json();
}
```

## 🧪 Development

### Running Linter

```bash
npm run lint
```

### Type Checking

```bash
npm run build
```

TypeScript type checking is integrated into the build process.

### Hot Module Replacement (HMR)

Vite provides fast HMR out of the box. Changes to React components will be reflected instantly without full page reload.

## 🎨 Styling

This project uses **Tailwind CSS** for styling. 

### Tailwind Configuration

Customize Tailwind in `tailwind.config.js`:

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Custom colors, fonts, etc.
    },
  },
  plugins: [],
}
```

### CSS Organization

- `src/index.css`: Global styles and Tailwind directives
- `src/App.css`: App-specific styles
- Inline Tailwind classes: Component-level styling

## 🔐 Security

- **Environment Variables**: Use `VITE_` prefix for public env vars
- **API Security**: Ensure API backend has proper CORS configuration
- **Content Security Policy**: Configure in CloudFront/hosting provider
- **HTTPS**: Always use HTTPS in production (CloudFront provides this)

## 📊 Performance

### Build Optimization

Vite automatically:
- Code splits by route
- Minifies JavaScript and CSS
- Optimizes assets
- Generates source maps for debugging

### CloudFront Caching

When deployed to CloudFront:
- Static assets cached at edge locations
- Versioned filenames for cache busting
- Fast global delivery

## 🆘 Troubleshooting

### Common Issues

**Port 5173 Already in Use**
```bash
# Vite will automatically try the next available port
npm run dev
# Or specify a different port
npm run dev -- --port 5174
```

**Build Fails with TypeScript Errors**
```bash
# Check for type errors
npx tsc --noEmit
```

**API Connection Fails**
- Ensure node-server is running
- Check `VITE_API_URL` environment variable
- Verify CORS settings in node-server
- Check browser console for error messages

**Styles Not Loading**
```bash
# Rebuild Tailwind
npm run build
```

### Debug Mode

```bash
# Run with debug output
DEBUG=vite:* npm run dev
```

## 🤝 Integration with Other Services

This client integrates with:
- **node-server**: Backend API for querying homework data
- **DynamoDB**: (via node-server) Homework data storage

Data flow:
```
User → React Client → node-server API → DynamoDB
```

## 📦 Dependencies

### Production Dependencies
- `react`: ^19.2.0
- `react-dom`: ^19.2.0

### Development Dependencies
- `@vitejs/plugin-react`: React plugin for Vite
- `typescript`: TypeScript compiler
- `vite`: Build tool and dev server
- `tailwindcss`: Utility-first CSS framework
- `eslint`: Linting tool

## 🔄 Updating Dependencies

```bash
# Check for outdated packages
npm outdated

# Update packages
npm update

# Update to latest versions (use with caution)
npx npm-check-updates -u
npm install
```

## 📄 License

MIT License - see main repository LICENSE file for details

## 🔗 Related Documentation

- [Main Project README](../README.md)
- [Node.js Server README](../node-server/README.md)
- [Node.js Scraper README](../node-scraper/README.md)
- [Lambda Deployment Guide](../node-scraper/LAMBDA_DEPLOYMENT.md)

## 💡 Contributing

1. Create a feature branch
2. Make your changes
3. Test locally with `npm run dev`
4. Build to ensure no errors: `npm run build`
5. Run linter: `npm run lint`
6. Submit a pull request
