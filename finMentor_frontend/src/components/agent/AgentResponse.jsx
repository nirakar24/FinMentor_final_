import { motion } from 'framer-motion';
import PropTypes from 'prop-types';

const AgentResponse = ({ response }) => {
  if (!response) return null;

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'border-danger-500 bg-danger-50';
      case 'medium':
        return 'border-warning-500 bg-warning-50';
      case 'low':
        return 'border-success-500 bg-success-50';
      default:
        return 'border-primary-500 bg-primary-50';
    }
  };

  const getPriorityBadgeColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'badge-danger';
      case 'medium':
        return 'badge-warning';
      case 'low':
        return 'badge-success';
      default:
        return 'badge-info';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* AI Answer Card */}
      <div className="card bg-gradient-to-br from-primary-50 to-primary-100 border-2 border-primary-300">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-600 to-primary-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold text-primary-900 mb-3 flex items-center gap-2">
              AI Financial Advice
              <span className="text-xs font-normal text-primary-700 bg-primary-200 px-2 py-1 rounded">
                Powered by LangGraph
              </span>
            </h3>
            <p className="text-slate-800 text-lg leading-relaxed whitespace-pre-wrap">
              {response.final_response}
            </p>
          </div>
        </div>
      </div>

      {/* Top Risks */}
      {response.top_risks && response.top_risks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <h4 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-danger-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            Top Risk Factors
          </h4>
          <div className="flex flex-wrap gap-2">
            {response.top_risks.map((risk, index) => (
              <motion.span
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="badge-danger text-sm"
              >
                {risk.replace(/_/g, ' ')}
              </motion.span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Behavioral Warnings */}
      {response.behavioral_warnings && response.behavioral_warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <h4 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-warning-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            Behavioral Warnings
          </h4>
          <div className="flex flex-wrap gap-2">
            {response.behavioral_warnings.map((warning, index) => (
              <motion.span
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                className="badge-warning text-sm"
              >
                {warning.replace(/_/g, ' ')}
              </motion.span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Action Steps */}
      {response.action_steps && response.action_steps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h4 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-success-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
            Recommended Action Steps
          </h4>
          <div className="space-y-4">
            {response.action_steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className={`border-l-4 p-4 rounded-r-lg ${getPriorityColor(step.priority)}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h5 className="font-bold text-slate-900">{step.title}</h5>
                      <span className={`${getPriorityBadgeColor(step.priority)} text-xs`}>
                        {step.priority}
                      </span>
                    </div>
                    <p className="text-slate-700">{step.description}</p>
                  </div>
                  <div className="flex-shrink-0">
                    <input
                      type="checkbox"
                      className="w-5 h-5 text-primary-600 border-2 border-slate-300 rounded focus:ring-2 focus:ring-primary-500 cursor-pointer"
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-slate-500">
        <p>Generated at: {new Date(response.generated_at).toLocaleString()}</p>
      </div>
    </motion.div>
  );
};

AgentResponse.propTypes = {
  response: PropTypes.shape({
    user_id: PropTypes.string,
    final_response: PropTypes.string.isRequired,
    top_risks: PropTypes.arrayOf(PropTypes.string),
    behavioral_warnings: PropTypes.arrayOf(PropTypes.string),
    action_steps: PropTypes.arrayOf(
      PropTypes.shape({
        title: PropTypes.string.isRequired,
        description: PropTypes.string.isRequired,
        priority: PropTypes.string.isRequired,
      })
    ),
    generated_at: PropTypes.string.isRequired,
  }),
};

export default AgentResponse;
