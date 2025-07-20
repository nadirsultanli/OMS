# LPG-OMS Frontend

A professional React-based admin panel for the LPG Order Management System by Circle.

## Features

- Professional login page with company branding
- Email/password authentication
- Forgot password functionality (placeholder for future API integration)
- Responsive design optimized for admin panels
- Token-based authentication with automatic refresh
- Protected routes
- Clean, modern UI design

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn
- LPG-OMS Backend API running on localhost:8000 (or update .env for different URL)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
   - Update `.env` file with correct API URLs
   - Set `REACT_APP_ENVIRONMENT` to "development" or "production"

3. Start the development server:
```bash
npm start
```

The application will open in your browser at `http://localhost:3000`.

## Environment Configuration

The `.env` file contains:
- `REACT_APP_API_URL_DEV`: Development API URL (default: http://localhost:8000)
- `REACT_APP_API_URL_PROD`: Production API URL
- `REACT_APP_ENVIRONMENT`: Current environment (development/production)

## Authentication Flow

1. User enters email and password on login page
2. Frontend sends credentials to `/auth/login` endpoint
3. Backend validates and returns JWT tokens + user info
4. Tokens are stored in localStorage
5. All subsequent API calls include Authorization header
6. Automatic token refresh when access token expires
7. Redirect to login if refresh fails

## API Integration

The frontend is configured to work with the FastAPI backend:
- Login: `POST /auth/login`
- Logout: `POST /auth/logout`
- Token Refresh: `POST /auth/refresh`
- Forgot Password: Placeholder (to be implemented)

## File Structure

```
src/
├── components/          # Reusable components
│   └── ProtectedRoute.js
├── pages/              # Page components
│   ├── Login.js
│   ├── Login.css
│   ├── Dashboard.js
│   └── Dashboard.css
├── services/           # API services
│   ├── api.js         # Axios configuration
│   └── authService.js # Authentication methods
├── assets/            # Static assets
│   └── Logo.svg       # Company logo
├── App.js             # Main app component
├── App.css            # Global app styles
├── index.js           # Entry point
└── index.css          # Global CSS reset
```

## Available Scripts

- `npm start`: Starts development server
- `npm build`: Builds the app for production
- `npm test`: Runs tests
- `npm run eject`: Ejects from Create React App

## Design Principles

- Professional, clean interface suitable for admin panels
- Accessibility considerations (focus states, ARIA labels)
- Responsive design for various screen sizes
- Modern CSS with smooth transitions and animations
- Consistent color scheme and typography