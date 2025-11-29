import { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { getUserSnapshot } from '../api/snapshot';
import KPICard from '../components/ui/KPICard';
import SpendingChart from '../components/charts/SpendingChart';
import IncomeExpenseChart from '../components/charts/IncomeExpenseChart';
import AlertCard from '../components/dashboard/AlertCard';
import HealthScoreCircle from '../components/dashboard/HealthScoreCircle';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import { useToast } from '../components/ui/Toast';

const Dashboard = () => {
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

    fetchSnapshot();
  }, [user.userId, setSnapshot, setLoading, showToast]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="h-8 w-64 bg-slate-200 rounded skeleton mb-2"></div>
            <div className="h-4 w-96 bg-slate-200 rounded skeleton"></div>
          </div>
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
          <svg className="w-16 h-16 text-slate-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-xl font-bold text-slate-900 mb-2">No Data Available</h3>
          <p className="text-slate-600">Unable to load financial snapshot. Please try again.</p>
        </div>
      </div>
    );
  }

  const { profile, income, spending, savings, debt, financial_health_score, alerts } = snapshot;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <ToastContainer />
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Welcome back, {profile?.name || 'User'}! 👋
          </h1>
          <p className="text-slate-600 text-lg">
            Here's your financial overview for today
          </p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Monthly Income"
            value={income?.average_monthly || 0}
            prefix="₹"
            icon={
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
            }
            gradient="bg-gradient-to-br from-emerald-50 to-emerald-100"
          />

          <KPICard
            title="Monthly Expense"
            value={spending?.total_monthly || 0}
            prefix="₹"
            icon={
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
              </svg>
            }
            gradient="bg-gradient-to-br from-rose-50 to-rose-100"
          />

          <KPICard
            title="Savings Balance"
            value={savings?.current_balance || 0}
            prefix="₹"
            icon={
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
              </svg>
            }
            gradient="bg-gradient-to-br from-blue-50 to-blue-100"
          />

          <KPICard
            title="Emergency Fund"
            value={Number((savings?.emergency_fund_months || 0).toFixed(2))}
            suffix=" months"
            icon={
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
              </svg>
            }
            gradient="bg-gradient-to-br from-amber-50 to-amber-100"
          />
        </div>

        {/* Charts and Health Score */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <SpendingChart categories={spending?.categories || []} />
          </div>
          <div>
            <HealthScoreCircle score={financial_health_score || 0} />
          </div>
        </div>

        {/* Income vs Expense Chart */}
        <div className="mb-8">
          <IncomeExpenseChart
            monthlyIncome={income?.average_monthly || 0}
            monthlyExpense={spending?.total_monthly || 0}
          />
        </div>

        {/* Alerts */}
        <div>
          <AlertCard alerts={alerts} />
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-600">Income Stability</p>
                <p className="text-2xl font-bold text-slate-900">{income?.stability_score || 0}%</p>
              </div>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${income?.stability_score || 0}%` }}
              />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-warning-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-warning-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-600">Discretionary Spending</p>
                <p className="text-2xl font-bold text-slate-900">
                  {((spending?.discretionary_ratio || 0) * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-warning-600 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${(spending?.discretionary_ratio || 0) * 100}%` }}
              />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-success-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-slate-600">Monthly Savings Rate</p>
                <p className="text-2xl font-bold text-slate-900">
                  {((savings?.monthly_savings_rate || 0) * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-success-600 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${(savings?.monthly_savings_rate || 0) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
