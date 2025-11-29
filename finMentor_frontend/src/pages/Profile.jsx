import { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { getUserSnapshot } from '../api/snapshot';
import HealthScoreCircle from '../components/dashboard/HealthScoreCircle';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import { useToast } from '../components/ui/Toast';
import { motion } from 'framer-motion';

const Profile = () => {
  const { user, snapshot, setSnapshot, loading, setLoading } = useApp();
  const { showToast, ToastContainer } = useToast();

  useEffect(() => {
    const fetchSnapshot = async () => {
      setLoading(true);
      try {
        const data = await getUserSnapshot(user.userId);
        setSnapshot(data);
      } catch (error) {
        showToast(error.message, 'error');
      } finally {
        setLoading(false);
      }
    };

    if (!snapshot) {
      fetchSnapshot();
    }
  }, [user.userId, snapshot, setSnapshot, setLoading, showToast]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-5xl mx-auto">
          <SkeletonLoader count={4} />
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-6">
        <ToastContainer />
        <div className="card text-center max-w-md">
          <h3 className="text-xl font-bold text-slate-900 mb-2">No Profile Data</h3>
          <p className="text-slate-600">Unable to load user profile. Please try again.</p>
        </div>
      </div>
    );
  }

  const { profile, income, spending, savings, debt, financial_health_score } = snapshot;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <ToastContainer />
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-slate-900 mb-2">User Profile</h1>
          <p className="text-slate-600 text-lg">Complete financial overview for {profile?.name}</p>
        </motion.div>

        {/* Profile Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card bg-gradient-to-br from-primary-50 to-primary-100 mb-8"
        >
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="w-24 h-24 bg-gradient-to-br from-primary-600 to-primary-500 rounded-full flex items-center justify-center text-4xl font-bold text-white">
              {profile?.name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-3xl font-bold text-slate-900 mb-2">{profile?.name || 'User'}</h2>
              <div className="flex flex-wrap gap-3 justify-center md:justify-start">
                <span className="badge-info">
                  {profile?.persona?.replace(/_/g, ' ') || 'N/A'}
                </span>
                <span className="badge bg-slate-200 text-slate-700">
                  Age: {profile?.age || 'N/A'}
                </span>
                <span className="badge bg-slate-200 text-slate-700">
                  📍 {profile?.location || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Income Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-900">Income</h3>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-slate-600">Average Monthly</p>
                <p className="text-2xl font-bold text-slate-900">
                  ₹{income?.average_monthly?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Stability Score</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-emerald-600 h-2 rounded-full transition-all duration-1000"
                      style={{ width: `${income?.stability_score || 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-slate-900">
                    {income?.stability_score || 0}%
                  </span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Savings Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-900">Savings</h3>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-slate-600">Current Balance</p>
                <p className="text-2xl font-bold text-slate-900">
                  ₹{savings?.current_balance?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Emergency Fund</p>
                <p className="text-lg font-semibold text-blue-600">
                  {savings?.emergency_fund_months?.toFixed(2) || 0} months
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Monthly Savings Rate</p>
                <p className="text-lg font-semibold text-slate-900">
                  {((savings?.monthly_savings_rate || 0) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </motion.div>

          {/* Debt Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-rose-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-rose-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-slate-900">Debt</h3>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-slate-600">Total Outstanding</p>
                <p className="text-2xl font-bold text-slate-900">
                  ₹{debt?.total_outstanding?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Monthly EMI</p>
                <p className="text-lg font-semibold text-rose-600">
                  ₹{debt?.monthly_emi?.toLocaleString() || 0}
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Spending Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card mb-8"
        >
          <h3 className="text-xl font-bold text-slate-900 mb-4">Spending Summary</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-200">
              <span className="text-slate-600 font-medium">Total Monthly Spending</span>
              <span className="text-2xl font-bold text-slate-900">
                ₹{spending?.total_monthly?.toLocaleString() || 0}
              </span>
            </div>
            <div className="flex justify-between items-center pb-3 border-b border-slate-200">
              <span className="text-slate-600 font-medium">Discretionary Ratio</span>
              <span className="text-lg font-semibold text-warning-600">
                {((spending?.discretionary_ratio || 0) * 100).toFixed(1)}%
              </span>
            </div>
            
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">Category Breakdown</h4>
              <div className="space-y-2">
                {spending?.categories?.map((category, index) => {
                  const percentage = ((category.amount / spending.total_monthly) * 100).toFixed(1);
                  return (
                    <div key={index} className="flex items-center gap-3">
                      <span className="text-sm font-medium text-slate-700 w-24">
                        {category.category}
                      </span>
                      <div className="flex-1 bg-slate-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all duration-1000"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-slate-900 w-24 text-right">
                        ₹{category.amount.toLocaleString()}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Health Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <HealthScoreCircle score={financial_health_score || 0} />
        </motion.div>
      </div>
    </div>
  );
};

export default Profile;
