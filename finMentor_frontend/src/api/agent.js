import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const runAgent = async (userId, userQuery) => {
  try {
    const response = await api.post('/agent/run', {
      user_id: userId,
      query: userQuery,
    });

    const data = response.data;

    // Transform the response to match our component expectations
    return {
      user_id: data.user_id,
      final_response: data.final_response || data.advice?.summary || 'No response generated',
      top_risks: data.advice?.top_risks || data.behavior_output?.behavior_flags || [],
      behavioral_warnings: data.advice?.behavioral_warnings || [],
      action_steps: data.action_items || data.advice?.action_steps || [],
      generated_at: data.advice?.generated_at || new Date().toISOString(),
      // Include raw data for detailed view
      snapshot: data.snapshot,
      rules_output: data.rules_output,
      behavior_output: data.behavior_output,
      advice: data.advice,
    };
  } catch (error) {
    throw new Error(error.response?.data?.message || 'Failed to run agent');
  }
};

export default { runAgent };
