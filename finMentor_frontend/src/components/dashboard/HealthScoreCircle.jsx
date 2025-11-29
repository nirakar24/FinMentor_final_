import PropTypes from 'prop-types';
import { motion } from 'framer-motion';

const HealthScoreCircle = ({ score }) => {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getColor = (score) => {
    if (score >= 70) return '#22c55e';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const getGrade = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Attention';
  };

  return (
    <div className="card text-center">
      <h3 className="text-xl font-bold text-slate-900 mb-6">Financial Health Score</h3>
      
      <div className="relative inline-block">
        <svg width="200" height="200" className="transform -rotate-90">
          <circle
            cx="100"
            cy="100"
            r={radius}
            stroke="#e2e8f0"
            strokeWidth="16"
            fill="none"
          />
          <motion.circle
            cx="100"
            cy="100"
            r={radius}
            stroke={getColor(score)}
            strokeWidth="16"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeInOut" }}
          />
        </svg>
        
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: "spring" }}
          >
            <p className="text-5xl font-bold" style={{ color: getColor(score) }}>
              {score}
            </p>
            <p className="text-sm text-slate-600 font-medium">out of 100</p>
          </motion.div>
        </div>
      </div>
      
      <div className="mt-6">
        <span
          className="px-4 py-2 rounded-full text-sm font-semibold"
          style={{
            backgroundColor: `${getColor(score)}20`,
            color: getColor(score),
          }}
        >
          {getGrade(score)}
        </span>
      </div>
    </div>
  );
};

HealthScoreCircle.propTypes = {
  score: PropTypes.number.isRequired,
};

export default HealthScoreCircle;
