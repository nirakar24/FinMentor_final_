import { motion } from 'framer-motion';

const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="relative">
        <motion.div
          className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 border-4 border-primary-100 border-t-primary-400 rounded-full"
          animate={{ rotate: -360 }}
          transition={{ duration: 0.7, repeat: Infinity, ease: "linear" }}
        />
      </div>
    </div>
  );
};

export default LoadingSpinner;
