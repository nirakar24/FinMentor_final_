import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const Toast = ({ message, type = 'error', duration = 3000, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const bgColor = {
    error: 'bg-danger-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    info: 'bg-primary-500',
  }[type];

  return (
    <motion.div
      initial={{ opacity: 0, y: -50, x: '-50%' }}
      animate={{ opacity: 1, y: 0, x: '-50%' }}
      exit={{ opacity: 0, y: -50, x: '-50%' }}
      className={`fixed top-4 left-1/2 transform ${bgColor} text-white px-6 py-3 rounded-lg shadow-xl z-50 flex items-center gap-3`}
    >
      <span className="font-medium">{message}</span>
      <button
        onClick={onClose}
        className="ml-2 text-white hover:text-slate-200 transition-colors"
      >
        ✕
      </button>
    </motion.div>
  );
};

Toast.propTypes = {
  message: PropTypes.string.isRequired,
  type: PropTypes.oneOf(['error', 'success', 'warning', 'info']),
  duration: PropTypes.number,
  onClose: PropTypes.func.isRequired,
};

export const useToast = () => {
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'error', duration = 3000) => {
    setToast({ message, type, duration });
  };

  const ToastContainer = () => (
    <AnimatePresence>
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => setToast(null)}
        />
      )}
    </AnimatePresence>
  );

  return { showToast, ToastContainer };
};

export default Toast;
