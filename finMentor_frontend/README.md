# FinMentor - AI Financial Coaching Dashboard

A production-grade, modern financial coaching dashboard built with React, Tailwind CSS, Chart.js, and Framer Motion. This frontend connects to a LangGraph + FastAPI Financial Coaching Agent Backend to provide personalized financial advice.

## 🚀 Features

- **Real-time Financial Analytics** - Track income, expenses, savings, and emergency funds
- **AI-Powered Advice** - LangGraph-powered financial coaching agent
- **Risk Detection** - Identify financial risks and behavioral patterns
- **Beautiful Visualizations** - Interactive charts with Chart.js
- **Responsive Design** - Mobile-first UI that works on all devices
- **Smooth Animations** - Subtle animations with Framer Motion
- **Action Plans** - Step-by-step guidance to achieve financial goals

## 🛠️ Tech Stack

- **React 18** with Vite
- **Tailwind CSS** for styling
- **Chart.js** & react-chartjs-2 for data visualization
- **Framer Motion** for animations
- **React Router** for navigation
- **Axios** for API calls

## 📦 Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🔌 Backend API

The frontend connects to: `http://localhost:8000`

### API Endpoints

#### 1. Run LangGraph Agent
```
POST /agent/run
```

**Request:**
```json
{
  "user_id": "GIG_001",
  "user_query": "When can I buy an iPhone?"
}
```

**Response:**
```json
{
  "user_id": "GIG_001",
  "final_response": "You can buy an iPhone in 2 months...",
  "top_risks": ["high_discretionary_spender"],
  "behavioral_warnings": ["unstable_cashflow"],
  "action_steps": [
    {
      "title": "Build Emergency Fund",
      "description": "Save ₹1,44,000",
      "priority": "high"
    }
  ],
  "generated_at": "2025-11-29T01:27:27Z"
}
```

#### 2. User Snapshot
```
GET /snapshot/{user_id}
```

**Response:**
```json
{
  "user_id": "GIG_001",
  "profile": {
    "name": "Rajesh Kumar",
    "persona": "gig_worker",
    "age": 28,
    "location": "Mumbai"
  },
  "income": {
    "average_monthly": 55000,
    "stability_score": 42
  },
  "spending": {
    "total_monthly": 48000,
    "discretionary_ratio": 0.31,
    "categories": [
      {"category": "Food", "amount": 12000}
    ]
  },
  "savings": {
    "current_balance": 12000,
    "emergency_fund_months": 0.22,
    "monthly_savings_rate": 0.13
  },
  "debt": {
    "total_outstanding": 45000,
    "monthly_emi": 3500
  },
  "financial_health_score": 38,
  "alerts": ["Emergency fund below 1 month"]
}
```

## 📁 Project Structure

```
src/
├── api/
│   ├── agent.js           # Agent API calls
│   └── snapshot.js        # Snapshot API calls
├── components/
│   ├── agent/
│   │   ├── AgentResponse.jsx    # AI response display
│   │   └── LoadingAgent.jsx     # Agent loading state
│   ├── charts/
│   │   ├── SpendingChart.jsx    # Doughnut chart
│   │   └── IncomeExpenseChart.jsx # Bar chart
│   ├── dashboard/
│   │   ├── AlertCard.jsx        # Financial alerts
│   │   └── HealthScoreCircle.jsx # Circular progress
│   └── ui/
│       ├── KPICard.jsx          # Animated KPI cards
│       ├── LoadingSpinner.jsx   # Loading spinner
│       ├── SkeletonLoader.jsx   # Skeleton screens
│       ├── Toast.jsx            # Toast notifications
│       └── Navbar.jsx           # Navigation bar
├── context/
│   └── AppContext.jsx     # Global state management
├── pages/
│   ├── Landing.jsx        # Landing page
│   ├── Dashboard.jsx      # Financial dashboard
│   ├── AgentRun.jsx       # AI agent interface
│   └── Profile.jsx        # User profile
├── App.jsx                # Main app component
├── main.jsx               # Entry point
└── index.css              # Global styles
```

## 🎨 Design Features

- **Gradient backgrounds** with soft colors
- **Smooth hover effects** on all interactive elements
- **Card-based layout** with shadows and rounded corners
- **Responsive grid system** that adapts to screen size
- **Custom scrollbar** styling
- **Loading states** with skeleton screens and spinners
- **Toast notifications** for user feedback
- **Animated counters** for KPI values
- **Chart.js visualizations** with custom tooltips

## 🔄 Routing

| Route        | Component    | Description             |
|--------------|--------------|-------------------------|
| `/`          | Landing      | Welcome page            |
| `/dashboard` | Dashboard    | Financial overview      |
| `/agent`     | AgentRun     | AI coaching interface   |
| `/profile`   | Profile      | User details & stats    |

## 🎯 Key Components

### KPICard
Animated card displaying key performance indicators with icons and optional change percentage.

### SpendingChart
Doughnut chart showing spending breakdown by category with interactive tooltips.

### IncomeExpenseChart
Bar chart comparing income vs expenses over the last 6 months.

### AgentResponse
Displays AI-generated financial advice with risk factors, warnings, and action steps.

### HealthScoreCircle
Animated circular progress bar showing financial health score (0-100).

## 🌟 State Management

Uses React Context API for global state:
- User information
- Financial snapshot data
- Agent responses
- Loading states
- Error handling

## 🎭 Animations

Framer Motion animations include:
- Page transitions
- Card hover effects
- Loading spinners
- Staggered list animations
- Scroll-based reveals

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints: `sm`, `md`, `lg`, `xl`
- Collapsible mobile navigation
- Touch-friendly UI elements
- Optimized for all screen sizes

## 🔧 Configuration

### Tailwind Config
Custom colors, animations, and utilities defined in `tailwind.config.js`

### API Base URL
Update in `src/api/agent.js` and `src/api/snapshot.js`:
```javascript
const BASE_URL = 'http://localhost:8000';
```

## 🚦 Getting Started

1. **Start the backend server** (ensure it's running on port 8000)
2. **Install dependencies**: `npm install`
3. **Run the dev server**: `npm run dev`
4. **Open**: `http://localhost:5173`

## 📝 Environment Variables

Create a `.env` file if needed:
```
VITE_API_BASE_URL=http://localhost:8000
```

Then update API files to use:
```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL;
```

## 🎨 Customization

### Colors
Edit `tailwind.config.js` to change the color scheme:
```javascript
colors: {
  primary: { ... },
  success: { ... },
  danger: { ... },
  warning: { ... }
}
```

### Animations
Modify animation timing in `tailwind.config.js`:
```javascript
animation: {
  'fade-in': 'fadeIn 0.5s ease-in-out',
  'slide-up': 'slideUp 0.4s ease-out'
}
```

## 🐛 Error Handling

- Toast notifications for API errors
- Fallback UI for missing data
- Loading states during async operations
- Graceful degradation

## 📊 Chart Configuration

Charts are configured with:
- Custom tooltips
- Responsive sizing
- Legend positioning
- Color palettes
- Hover effects

## 🔒 Best Practices

- Component prop validation with PropTypes
- Clean code structure
- Reusable components
- Semantic HTML
- Accessibility considerations
- Performance optimization

## 📚 Learn More

- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Chart.js](https://www.chartjs.org)
- [Framer Motion](https://www.framer.com/motion)
- [Vite](https://vitejs.dev)

## 🤝 Contributing

This is a production-grade application. Follow the existing code style and component structure when making changes.

## 📄 License

MIT License - feel free to use this project for your own purposes.

---

Built with ❤️ using React, Tailwind CSS, Chart.js, and Framer Motion
