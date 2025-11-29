const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

class ApiService {
    /**
     * Onboard a user - Creates consent
     * @param {string} mobileNumber - User's mobile number
     */
    async onboardUser(mobileNumber) {
        try {
            const response = await fetch(`${API_BASE_URL}/User/onboard`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mobileNumber }),
            });
            console.log(response);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to onboard user');
            }

            return await response.json();
        } catch (error) {
            console.error('Error onboarding user:', error);
            throw error;
        }
    }

    /**
     * Get consent data directly
     * @param {string} mobileNumber - User's mobile number
     */
    async getConsentData(mobileNumber) {
        try {
            const response = await fetch(`${API_BASE_URL}/Consent/data?mobileNumber=${mobileNumber}`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch consent data');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching consent data:', error);
            throw error;
        }
    }

    /**
     * Get transaction history for a user
     * @param {string} mobileNumber - User's mobile number
     * @param {string} from - Start date (optional)
     * @param {string} to - End date (optional)
     */
    async getTransactions(mobileNumber, from = '', to = '') {
        try {
            const params = new URLSearchParams({ mobileNumber });
            if (from) params.append('from', from);
            if (to) params.append('to', to);

            const response = await fetch(`${API_BASE_URL}/user/transactions?${params.toString()}`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch transactions');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching transactions:', error);
            throw error;
        }
    }

    /**
     * Create a new consent
     * @param {string} vua - Virtual User Address (e.g., mobile@onemoney)
     * @param {object} dataRange - Date range for consent
     */
    async createConsent(vua, dataRange) {
        try {
            const response = await fetch(`${API_BASE_URL}/consents/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ vua, dataRange }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to create consent');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating consent:', error);
            throw error;
        }
    }

    /**
     * Fetch data for a consent ID
     * @param {string} consentId - Consent ID
     */
    async fetchConsentData(consentId) {
        try {
            const response = await fetch(`${API_BASE_URL}/consents/${consentId}/fetch`, {
                method: 'POST',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch consent data');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching consent data:', error);
            throw error;
        }
    }
}

export default new ApiService();
