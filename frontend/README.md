# FinMentor Frontend

A modern, beautiful React + Vite frontend application for the Setu Account Aggregator platform.

## 🚀 Features

- **User Onboarding**: Seamlessly onboard users and connect their financial accounts
- **Transaction History**: View and filter transaction data with beautiful UI
- **Consent Management**: Handle consent creation and data fetching
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Modern UI**: Built with Tailwind CSS featuring gradients, animations, and glassmorphism

## 🛠️ Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript (ES6+)** - Programming language

## 📦 Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Update `VITE_API_BASE_URL` with your backend API URL
   ```bash
   cp .env.example .env
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── OnboardUser.jsx       # User onboarding component
│   │   └── TransactionHistory.jsx # Transaction listing component
│   ├── services/
│   │   └── api.js                 # API service layer
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # App entry point
│   └── index.css                  # Global styles with Tailwind
├── public/                        # Static assets
├── .env                           # Environment variables
├── .env.example                   # Environment variables template
├── tailwind.config.js             # Tailwind configuration
├── postcss.config.js              # PostCSS configuration
├── vite.config.js                 # Vite configuration
└── package.json                   # Dependencies
```

## 🎨 Components

### OnboardUser
Allows users to onboard by providing their mobile number and optional consent ID. Handles the entire consent flow and account data fetching.

**Features**:
- Mobile number validation
- Optional consent ID input
- Loading states
- Success/error feedback
- Beautiful animations

### TransactionHistory
Displays transaction history for a user with optional date range filtering.

**Features**:
- Mobile number search
- Date range filtering
- Transaction categorization (credit/debit)
- Currency formatting
- Scrollable transaction list
- Empty state handling

## 🔌 API Integration

The frontend connects to the SetuDemo backend API. Configure the API base URL in `.env`:

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

### Available API Endpoints

1. **POST /api/user/onboard**
   - Onboard a user and fetch account data
   - Body: `{ mobileNumber, consentId? }`

2. **GET /api/user/transactions**
   - Get transaction history
   - Query params: `mobileNumber`, `from?`, `to?`

3. **POST /api/consents/create**
   - Create a new consent
   - Body: `{ vua, dataRange }`

4. **POST /api/consents/{consentId}/fetch**
   - Fetch data for a consent

## 🎨 Styling

The app uses Tailwind CSS with custom configurations:

- **Custom Colors**: Primary (blue) and Secondary (purple) palettes
- **Custom Animations**: Fade-in, slide-up, pulse effects
- **Glassmorphism**: Backdrop blur effects for modern UI
- **Gradients**: Beautiful gradient backgrounds and text
- **Inter Font**: Modern, clean typography

## 🚀 Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## 🧪 Development

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📱 Responsive Design

The application is fully responsive with breakpoints:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## 🎯 Key Features

### Beautiful UI/UX
- Gradient backgrounds
- Smooth animations and transitions
- Hover effects and micro-interactions
- Loading states with spinners
- Success/error notifications
- Card-based layout with glassmorphism

### Performance
- Vite for fast HMR (Hot Module Replacement)
- Optimized production builds
- Code splitting
- Lazy loading ready

### Developer Experience
- Clean component structure
- Reusable API service layer
- Environment-based configuration
- ESLint configuration included

## 🔧 Configuration

### Tailwind Config
Custom theme extensions in `tailwind.config.js`:
- Color palette
- Animations
- Font families

### Vite Config
Optimized build settings in `vite.config.js`

## 📝 License

© 2025 FinMentor. All rights reserved.

## 🤝 Contributing

This is a demo application for the Setu Account Aggregator integration.

---

**Powered by Setu Account Aggregator** 🚀
