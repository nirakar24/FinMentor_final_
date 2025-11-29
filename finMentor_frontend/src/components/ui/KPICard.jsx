import { motion } from 'framer-motion';
import PropTypes from 'prop-types';
import { useEffect, useState } from 'react';

const AnimatedCounter = ({ value, duration = 2000, suffix = '', prefix = '' }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime;
    let animationFrame;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      const percentage = Math.min(progress / duration, 1);
      
      setCount(Math.floor(value * percentage));

      if (percentage < 1) {
        animationFrame = requestAnimationFrame(animate);
      } else {
        setCount(value);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  return (
    <span>
      {prefix}{count.toLocaleString()}{suffix}
    </span>
  );
};

AnimatedCounter.propTypes = {
  value: PropTypes.number.isRequired,
  duration: PropTypes.number,
  suffix: PropTypes.string,
  prefix: PropTypes.string,
};

const KPICard = ({ title, value, icon, gradient, suffix = '', prefix = '', change }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.05, y: -5 }}
      transition={{ duration: 0.3 }}
      className={`card-gradient ${gradient} overflow-hidden relative`}
    >
      <div className="absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 opacity-10">
        {icon}
      </div>
      
      <div className="relative z-10">
        <p className="text-sm font-medium text-slate-600 mb-2">{title}</p>
        <h3 className="text-3xl font-bold text-slate-900 mb-1">
          <AnimatedCounter value={value} prefix={prefix} suffix={suffix} />
        </h3>
        {change !== undefined && (
          <p className={`text-sm font-medium ${change >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
          </p>
        )}
      </div>
    </motion.div>
  );
};

KPICard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  icon: PropTypes.node.isRequired,
  gradient: PropTypes.string.isRequired,
  suffix: PropTypes.string,
  prefix: PropTypes.string,
  change: PropTypes.number,
};

export default KPICard;
