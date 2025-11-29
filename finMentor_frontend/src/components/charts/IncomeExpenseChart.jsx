import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import PropTypes from 'prop-types';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const IncomeExpenseChart = ({ monthlyIncome, monthlyExpense }) => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  
  // Generate realistic variance for demo
  const generateData = (base, variance = 0.15) => {
    return months.map(() => {
      const change = base * (Math.random() * variance * 2 - variance);
      return Math.round(base + change);
    });
  };

  const data = {
    labels: months,
    datasets: [
      {
        label: 'Income',
        data: generateData(monthlyIncome),
        backgroundColor: 'rgba(14, 165, 233, 0.8)',
        borderColor: 'rgba(14, 165, 233, 1)',
        borderWidth: 2,
        borderRadius: 6,
      },
      {
        label: 'Expense',
        data: generateData(monthlyExpense),
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2,
        borderRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          padding: 15,
          font: {
            size: 13,
            weight: '500',
          },
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
          weight: 'bold',
        },
        bodyFont: {
          size: 13,
        },
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          callback: function(value) {
            return '₹' + (value / 1000) + 'k';
          },
        },
      },
    },
  };

  return (
    <div className="card">
      <h3 className="text-xl font-bold text-slate-900 mb-6">Income vs Expense (Last 6 Months)</h3>
      <div className="h-80">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
};

IncomeExpenseChart.propTypes = {
  monthlyIncome: PropTypes.number.isRequired,
  monthlyExpense: PropTypes.number.isRequired,
};

export default IncomeExpenseChart;
