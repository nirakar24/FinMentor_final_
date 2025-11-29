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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <ToastContainer />
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <h1 className="text-4xl font-bold text-slate-900 mb-3">
            AI Financial Coach 🤖
          </h1>
          <p className="text-slate-600 text-lg">
            Ask anything about your finances and get personalized advice
          </p>
        </motion.div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card mb-8"
        >
          <form onSubmit={handleRunAgent} className="space-y-4">
            <div>
              <label htmlFor="userId" className="block text-sm font-semibold text-slate-700 mb-2">
                User ID
              </label>
              <input
                type="text"
                id="userId"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="input-field"
                placeholder="Enter user ID"
              />
            </div>

            <div>
              <label htmlFor="query" className="block text-sm font-semibold text-slate-700 mb-2">
                Your Question
              </label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="input-field resize-none"
                placeholder="e.g., When can I buy an iPhone?"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Run Financial Agent
                </span>
              )}
            </button>
          </form>
        </motion.div>

        {/* Loading State */}
        {loading && <LoadingAgent />}

        {/* Agent Response */}
        {!loading && agentResponse && <AgentResponse response={agentResponse} />}

        {/* Empty State */}
        {!loading && !agentResponse && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="card text-center py-16"
          >
            <div className="w-24 h-24 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-3">
              Ready to Assist
            </h3>
            <p className="text-slate-600 max-w-md mx-auto">
              Enter your question above and click "Run Financial Agent" to get personalized financial advice powered by AI
            </p>
          </motion.div>
        )}

        {/* Sample Questions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <h3 className="text-lg font-semibold text-slate-900 mb-4">💡 Sample Questions:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              'When can I buy an iPhone?',
              'How can I build an emergency fund?',
              'Should I invest in mutual funds?',
              'How do I reduce my expenses?',
            ].map((sample, index) => (
              <button
                key={index}
                onClick={() => setQuery(sample)}
                className="card hover:border-primary-300 border-2 border-transparent text-left transition-all"
              >
                <p className="text-slate-700">{sample}</p>
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default AgentRun;
