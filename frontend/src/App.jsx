import { useState } from 'react';
import OnboardUser from './components/OnboardUser';
import TransactionHistory from './components/TransactionHistory';

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  const handleNavClick = (tab) => {
    setActiveTab(tab);
    closeMobileMenu();
  };

  return (
    <div className="min-h-screen bg-[#f0fdf4] font-sans text-slate-800 selection:bg-emerald-200 selection:text-emerald-900">
      {/* Decorative Background Elements */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-emerald-200/20 blur-3xl"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-green-200/20 blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-emerald-100 shadow-sm transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            {/* Logo */}
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => handleNavClick('home')}
            >
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-200 group-hover:shadow-emerald-300 transition-all duration-300 group-hover:scale-105">
                <svg className="w-6 h-6 sm:w-7 sm:h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex flex-col">
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-emerald-700 to-green-600 bg-clip-text text-transparent tracking-tight">
                  FinMentor
                </h1>
                <span className="text-[10px] sm:text-xs font-medium text-emerald-600/80 tracking-wider uppercase">
                  Smart Money
                </span>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1 bg-emerald-50/50 p-1.5 rounded-2xl border border-emerald-100/50">
              {['home', 'onboard', 'transactions'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => handleNavClick(tab)}
                  className={`px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-300 relative overflow-hidden ${activeTab === tab
                      ? 'text-emerald-700 shadow-sm bg-white ring-1 ring-emerald-100'
                      : 'text-emerald-600 hover:text-emerald-800 hover:bg-emerald-100/50'
                    }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>

            {/* Mobile Menu Button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-xl text-emerald-700 hover:bg-emerald-50 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-200"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <div
          className={`md:hidden absolute top-full left-0 right-0 bg-white/95 backdrop-blur-xl border-b border-emerald-100 shadow-lg transition-all duration-300 origin-top ${isMobileMenuOpen ? 'opacity-100 scale-y-100 visible' : 'opacity-0 scale-y-95 invisible'
            }`}
        >
          <div className="px-4 py-4 space-y-2">
            {['home', 'onboard', 'transactions'].map((tab) => (
              <button
                key={tab}
                onClick={() => handleNavClick(tab)}
                className={`w-full text-left px-4 py-3 rounded-xl font-medium transition-all duration-200 ${activeTab === tab
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                    : 'text-slate-600 hover:bg-slate-50'
                  }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-24 sm:pt-28 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto min-h-[calc(100vh-80px)]">
        {activeTab === 'home' && (
          <div className="animate-fade-in space-y-12 sm:space-y-20">
            {/* Hero Section */}
            <div className="text-center max-w-4xl mx-auto mt-4 sm:mt-8">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100/80 text-emerald-700 text-xs sm:text-sm font-semibold mb-6 border border-emerald-200 animate-slide-up">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Start Saving Today
              </div>
              <h2 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-slate-900 tracking-tight mb-6 sm:mb-8 leading-tight">
                Grow Your Wealth <br className="hidden sm:block" />
                <span className="bg-gradient-to-r from-emerald-600 via-green-500 to-teal-500 bg-clip-text text-transparent">
                  One Rupee at a Time
                </span>
              </h2>
              <p className="text-lg sm:text-xl text-slate-600 mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed">
                Experience the future of personal finance. Securely connect your accounts, track expenses, and unlock personalized insights to maximize your savings.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto px-4 sm:px-0">
                <button
                  onClick={() => handleNavClick('onboard')}
                  className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white rounded-2xl font-bold shadow-lg shadow-emerald-200 hover:shadow-emerald-300 hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-center gap-2"
                >
                  Get Started
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
                <button
                  onClick={() => handleNavClick('transactions')}
                  className="w-full sm:w-auto px-8 py-4 bg-white text-slate-700 border border-slate-200 hover:border-emerald-200 hover:bg-emerald-50/50 rounded-2xl font-bold transition-all duration-300 flex items-center justify-center gap-2"
                >
                  View Demo
                </button>
              </div>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
              {[
                {
                  title: "Bank-Grade Security",
                  desc: "Your data is encrypted and secure. We use industry-standard protocols to ensure your financial information stays safe.",
                  icon: (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  ),
                  color: "emerald"
                },
                {
                  title: "Real-Time Tracking",
                  desc: "Monitor your transactions as they happen. Get instant updates and categorize your spending automatically.",
                  icon: (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  ),
                  color: "green"
                },
                {
                  title: "Smart Insights",
                  desc: "Receive personalized recommendations on how to save more based on your spending habits and financial goals.",
                  icon: (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  ),
                  color: "teal"
                }
              ].map((feature, idx) => (
                <div key={idx} className="group relative p-8 bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-emerald-100/50 transition-all duration-300 hover:-translate-y-1">
                  <div className={`w-14 h-14 rounded-2xl bg-${feature.color}-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <svg className={`w-7 h-7 text-${feature.color}-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {feature.icon}
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-slate-800 mb-3">{feature.title}</h3>
                  <p className="text-slate-600 leading-relaxed">
                    {feature.desc}
                  </p>
                </div>
              ))}
            </div>

            {/* Stats/Trust Section */}
            {/* <div className="bg-emerald-900 rounded-3xl p-8 sm:p-12 text-center text-white relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-full opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"></div>
              <div className="relative z-10">
                <h3 className="text-2xl sm:text-3xl font-bold mb-8">Trusted by thousands of savers</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                  {[
                    { label: "Active Users", value: "50K+" },
                    { label: "Transactions", value: "1M+" },
                    { label: "Banks Supported", value: "20+" },
                    { label: "Money Saved", value: "₹10Cr+" },
                  ].map((stat, idx) => (
                    <div key={idx}>
                      <div className="text-3xl sm:text-4xl font-bold text-emerald-400 mb-2">{stat.value}</div>
                      <div className="text-emerald-200 text-sm font-medium uppercase tracking-wider">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div> */}
          </div>
        )}

        {activeTab === 'onboard' && (
          <div className="max-w-2xl mx-auto animate-fade-in">
            <div className="bg-white rounded-3xl shadow-xl shadow-emerald-100/50 border border-emerald-100 overflow-hidden">
              <div className="bg-emerald-50/50 p-6 border-b border-emerald-100">
                <h2 className="text-2xl font-bold text-emerald-900">Connect Your Bank</h2>
                <p className="text-emerald-700 mt-1">Securely link your accounts to start tracking.</p>
              </div>
              <div className="p-6">
                <OnboardUser />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'transactions' && (
          <div className="max-w-5xl mx-auto animate-fade-in">
            <div className="bg-white rounded-3xl shadow-xl shadow-emerald-100/50 border border-emerald-100 overflow-hidden">
              <div className="bg-emerald-50/50 p-6 border-b border-emerald-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-emerald-900">Transaction History</h2>
                  <p className="text-emerald-700 mt-1">Your recent financial activity.</p>
                </div>
                <button className="px-4 py-2 bg-white text-emerald-700 text-sm font-semibold rounded-lg border border-emerald-200 hover:bg-emerald-50 transition-colors">
                  Download Report
                </button>
              </div>
              <div className="p-0">
                <TransactionHistory />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-100 py-12 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="font-bold text-slate-700">FinMentor</span>
            </div>
            <div className="text-slate-500 text-sm text-center md:text-right">
              <p>© 2025 FinMentor. All rights reserved.</p>
              <p className="mt-1">Powered by <span className="text-emerald-600 font-medium">Setu Account Aggregator</span></p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;