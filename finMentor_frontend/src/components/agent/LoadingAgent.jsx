import { motion } from 'framer-motion';

const LoadingAgent = () => {
  return (
    <div className="card text-center py-12">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mb-6"
      >
        <div className="relative inline-block">
          <motion.div
            className="w-24 h-24 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center shadow-lg shadow-emerald-200"
            animate={{
              scale: [1, 1.1, 1],
              rotate: [0, 180, 360],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </motion.div>

          {/* Pulsing rings */}
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute inset-0 border-4 border-emerald-400 rounded-full"
              initial={{ scale: 1, opacity: 1 }}
              animate={{
                scale: [1, 1.5, 2],
                opacity: [1, 0.5, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.4,
              }}
            />
          ))}
        </div>
      </motion.div>

      <h3 className="text-2xl font-bold text-emerald-900 mb-3">
        AI Agent Processing...
      </h3>

      <div className="space-y-2 mb-6">
        {[
          'Analyzing your financial snapshot',
          'Detecting spending patterns',
          'Calculating risk factors',
          'Generating personalized advice',
        ].map((text, index) => (
          <motion.p
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.3 }}
            className="text-emerald-700 font-medium"
          >
            {text}
          </motion.p>
        ))}
      </div>

      {/* Loading bar */}
      <div className="w-full max-w-md mx-auto h-2 bg-emerald-100 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-600 to-green-500"
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: 3, repeat: Infinity }}
        />
      </div>
    </div>
  );
};

export default LoadingAgent;
