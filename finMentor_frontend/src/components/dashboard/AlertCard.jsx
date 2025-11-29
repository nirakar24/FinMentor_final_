import { motion } from 'framer-motion';
import PropTypes from 'prop-types';

const AlertCard = ({ alerts }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="card bg-gradient-to-r from-success-50 to-success-100">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-success-500 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-bold text-success-900">All Clear!</h3>
            <p className="text-success-700">No critical alerts at this time</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-6 h-6 text-danger-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-xl font-bold text-slate-900">Financial Alerts</h3>
      </div>
      
      <div className="space-y-3">
        {alerts.map((alert, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-danger-50 border-l-4 border-danger-500 p-4 rounded"
          >
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-danger-800 font-medium">{alert}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

AlertCard.propTypes = {
  alerts: PropTypes.arrayOf(PropTypes.string),
};

export default AlertCard;
