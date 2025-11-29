import axios from 'axios';

const BASE_URL = 'http://localhost:8001';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getUserSnapshot = async (userId) => {
  try {
    const response = await api.get(`/snapshot/${userId}`);
    const data = response.data;

    // Handle both direct snapshot and nested snapshot response
    const snapshot = data.snapshot || data;

    return {
      user_id: snapshot.user_id,
      profile: snapshot.profile,
      income: snapshot.income,
      spending: snapshot.spending,
      savings: snapshot.savings,
      debt: snapshot.debt,
      financial_health_score: snapshot.financial_health_score,
      alerts: snapshot.alerts || [],
    };
  } catch (error) {
    throw new Error(error.response?.data?.message || 'Failed to fetch user snapshot');
  }
};

export default { getUserSnapshot };
