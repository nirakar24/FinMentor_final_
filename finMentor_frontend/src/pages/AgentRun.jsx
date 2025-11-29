import { useState } from 'react';
import { useApp } from '../context/AppContext';
import { runAgent } from '../api/agent';
import AgentResponse from '../components/agent/AgentResponse';
import LoadingAgent from '../components/agent/LoadingAgent';
import { useToast } from '../components/ui/Toast';
import { motion } from 'framer-motion';

const AgentRun = () => {
  const { user, agentResponse, setAgentResponse, loading, setLoading } = useApp();
  const [userId, setUserId] = useState(user.userId);
  const [query, setQuery] = useState('');
  const { showToast, ToastContainer } = useToast();

  const handleRunAgent = async (e) => {
    e.preventDefault();

    if (!query.trim()) {
      showToast('Please enter a question', 'warning');
      return;
    }

    setLoading(true);
    try {
      const response = await runAgent(userId, query);
      setAgentResponse(response);
      showToast('Agent completed successfully!', 'success');
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-emerald-100 p-6 font-sans">
      <ToastContainer />
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10 text-center"
        >
          <div className="inline-block p-3 rounded-2xl bg-emerald-100/50 mb-4 backdrop-blur-sm">
            <span className="text-4xl">🤖</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-800 to-teal-700 mb-4 tracking-tight">
            AI Financial Coach
          </h1>
          <p className="text-emerald-600/90 text-lg md:text-xl font-medium max-w-2xl mx-auto leading-relaxed">
            Your personal wealth advisor. Ask anything about your finances and get data-driven, personalized advice instantly.
          </p>
        </motion.div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl shadow-emerald-900/5 border border-emerald-100 overflow-hidden mb-10"
        >
          <div className="p-8 md:p-10">
            <form onSubmit={handleRunAgent} className="space-y-8">
              <div className="grid grid-cols-1 gap-8">
                <div>
                  <label htmlFor="userId" className="block text-sm font-bold text-emerald-800 uppercase tracking-wider mb-3">
                    User ID
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      id="userId"
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                      className="w-full px-5 py-4 bg-emerald-50/30 border border-emerald-200 rounded-xl focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all duration-300 text-emerald-900 placeholder-emerald-300 font-medium"
                      placeholder="Enter your user ID"
                    />
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-emerald-400">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="query" className="block text-sm font-bold text-emerald-800 uppercase tracking-wider mb-3">
                    Your Financial Question
                  </label>
                  <div className="relative">
                    <textarea
                      id="query"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      rows={4}
                      className="w-full px-5 py-4 bg-emerald-50/30 border border-emerald-200 rounded-xl focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 transition-all duration-300 text-emerald-900 placeholder-emerald-300 resize-none font-medium leading-relaxed"
                      placeholder="e.g., How much can I save this month based on my spending?"
                    />
                    <div className="absolute right-4 top-4 text-emerald-400">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 p-4 text-white shadow-lg shadow-emerald-500/30 transition-all duration-300 hover:scale-[1.01] hover:shadow-emerald-500/40 disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:scale-100"
              >
                <div className="absolute inset-0 bg-white/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                {loading ? (
                  <span className="flex items-center justify-center gap-3 font-bold text-lg">
                    <svg className="animate-spin h-6 w-6 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Analyzing Financial Data...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-3 font-bold text-lg">
                    <span>Run Analysis</span>
                    <svg className="w-6 h-6 transition-transform duration-300 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </span>
                )}
              </button>
            </form>
          </div>
        </motion.div>

        {/* Loading State */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-10"
          >
            <LoadingAgent />
          </motion.div>
        )}

        {/* Agent Response */}
        {!loading && agentResponse && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-10"
          >
            <AgentResponse response={agentResponse} />
          </motion.div>
        )}

        {/* Empty State */}
        {!loading && !agentResponse && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white/60 backdrop-blur-md rounded-3xl border-2 border-dashed border-emerald-200/50 p-12 text-center"
          >
            <div className="w-20 h-20 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
              <svg className="w-10 h-10 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-emerald-900 mb-3">
              Ready to Optimize Your Finances
            </h3>
            <p className="text-emerald-600/80 max-w-md mx-auto">
              Our AI analyzes your transaction history to provide actionable insights. Try asking one of the sample questions below.
            </p>
          </motion.div>
        )}

        {/* Sample Questions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-12"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="h-px flex-1 bg-emerald-200/50"></div>
            <h3 className="text-sm font-bold text-emerald-800 uppercase tracking-wider">Try these questions</h3>
            <div className="h-px flex-1 bg-emerald-200/50"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { icon: '📱', text: 'When can I afford to buy an iPhone?' },
              { icon: '💰', text: 'How can I start building an emergency fund?' },
              { icon: '📈', text: 'Should I invest in mutual funds right now?' },
              { icon: '✂️', text: 'What expenses should I cut to save more?' },
            ].map((sample, index) => (
              <button
                key={index}
                onClick={() => setQuery(sample.text)}
                className="group flex items-center gap-4 p-4 bg-white/70 hover:bg-white backdrop-blur-sm border border-emerald-100 hover:border-emerald-300 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-left"
              >
                <span className="text-2xl group-hover:scale-110 transition-transform duration-300">{sample.icon}</span>
                <span className="text-emerald-700 font-medium group-hover:text-emerald-900 transition-colors">{sample.text}</span>
                <svg className="w-5 h-5 text-emerald-300 group-hover:text-emerald-500 ml-auto opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AgentRun;
