# Swasthya Sakhi - React Version

This is a React.js implementation of the Swasthya Sakhi healthcare platform, originally built with Django. This React version maintains all the functionality and design of the original while leveraging modern frontend technologies.

## Features

- **World-Class UI Design**: Apple-grade polish with glassmorphism and smooth animations
- **Multi-Language Support**: English and Kannada (ಕನ್ನಡ) for rural accessibility
- **Healthcare Services**:
  - Government scheme eligibility checking with AI
  - Secure medical report storage and management
  - AI-powered medical report analysis
  - Premium subscription features

## Tech Stack

- **Frontend**: React.js with Vite
- **State Management**: React Hooks and Context API
- **Routing**: React Router v6
- **Styling**: CSS Modules with custom design system
- **Animations**: CSS Animations and Intersection Observer API
- **Internationalization**: Custom translation system

## Project Structure

```
arogyamitra-react/
├── public/                 # Static assets
├── src/
│   ├── components/         # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Page components
│   ├── services/           # API service layer
│   ├── utils/              # Utility functions
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
└── vite.config.js          # Vite configuration
```

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd arogyamitra-react
```

2. Install dependencies:
```bash
npm install
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Key Components

### Pages
- **Home**: Landing page with feature highlights
- **Scheme Checker**: AI-powered eligibility checking
- **Report Vault**: Secure medical report storage
- **Report Analysis**: AI interpretation of medical reports
- **Premium**: Subscription upgrade page
- **Login/Register**: Authentication flows
- **Hospital Dashboard**: Report upload interface for medical staff

### Components
- **Navbar**: Responsive navigation with language toggle
- **AnimatedSection**: Scroll-triggered animations
- **Particles**: Background particle effects
- **Form Components**: Validated form inputs with error handling
- **Notification System**: Toast notifications for user feedback

## Internationalization

The application supports both English and Kannada languages. Language preference is stored in localStorage and persists across sessions.

## Styling

The application uses a custom design system with:
- Glassmorphism effects
- Gradient color palette
- Responsive layouts
- Smooth animations and transitions
- Mobile-first approach

## State Management

Custom hooks are used for:
- Authentication state
- Report management
- Scheme eligibility checking
- Form validation
- Language preferences

## API Integration

The React frontend connects to the existing Django REST API backend, maintaining compatibility with all existing endpoints.

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Responsive design for mobile, tablet, and desktop

## Development Guidelines

- Follow component-driven development
- Use functional components with hooks
- Maintain consistent styling with the design system
- Implement proper error handling
- Write accessible code
- Optimize performance with lazy loading where appropriate

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is proprietary and confidential. All rights reserved.