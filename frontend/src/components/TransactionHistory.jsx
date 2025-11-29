import { useState } from 'react';
import apiService from '../services/api';

export default function TransactionHistory() {
    const [mobileNumber, setMobileNumber] = useState('');
    const [fromDate, setFromDate] = useState('');
    const [toDate, setToDate] = useState('');
    const [loading, setLoading] = useState(false);
    const [transactions, setTransactions] = useState([]);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setTransactions([]);

        try {
            const data = await apiService.getTransactions(mobileNumber, fromDate, toDate);
            setTransactions(data.transactions || data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
        }).format(amount);
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    return (
        <div className="animate-fade-in p-6">
            <form onSubmit={handleSubmit} className="space-y-6 mb-8">
                <div>
                    <label htmlFor="mobile-tx" className="block text-sm font-semibold text-emerald-900 mb-2">
                        Mobile Number <span className="text-red-500">*</span>
                    </label>
                    <input
                        id="mobile-tx"
                        type="tel"
                        placeholder="9999999999"
                        value={mobileNumber}
                        onChange={(e) => setMobileNumber(e.target.value)}
                        className="w-full px-4 py-3 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all bg-emerald-50/30 text-emerald-900 placeholder-emerald-300"
                        required
                        pattern="[0-9]{10}"
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="from-date" className="block text-sm font-semibold text-emerald-900 mb-2">
                            From Date <span className="text-emerald-400 text-xs">(Optional)</span>
                        </label>
                        <input
                            id="from-date"
                            type="date"
                            value={fromDate}
                            onChange={(e) => setFromDate(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all bg-emerald-50/30 text-emerald-900"
                        />
                    </div>

                    <div>
                        <label htmlFor="to-date" className="block text-sm font-semibold text-emerald-900 mb-2">
                            To Date <span className="text-emerald-400 text-xs">(Optional)</span>
                        </label>
                        <input
                            id="to-date"
                            type="date"
                            value={toDate}
                            onChange={(e) => setToDate(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl border border-emerald-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all bg-emerald-50/30 text-emerald-900"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3.5 rounded-xl text-base font-bold text-emerald-700 bg-emerald-100 hover:bg-emerald-200 border border-emerald-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <span className="flex items-center justify-center gap-2">
                            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Loading...
                        </span>
                    ) : (
                        'Get Transactions'
                    )}
                </button>
            </form>

            {error && (
                <div className="mb-8 p-4 bg-red-50 border border-red-100 rounded-xl animate-slide-up flex items-center gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                        <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <p className="text-red-700 font-medium text-sm">{error}</p>
                </div>
            )}

            {transactions.length > 0 && (
                <div className="animate-slide-up">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-emerald-900">
                            Found {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
                        </h3>
                    </div>

                    <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
                        {transactions.map((tx, index) => (
                            <div
                                key={index}
                                className="group bg-white p-5 rounded-2xl border border-slate-100 hover:border-emerald-200 hover:shadow-lg hover:shadow-emerald-50 transition-all duration-300"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${tx.type === 'CREDIT' || tx.amount > 0
                                                    ? 'bg-green-100 text-green-600'
                                                    : 'bg-red-100 text-red-600'
                                                }`}>
                                                {tx.type === 'CREDIT' || tx.amount > 0 ? (
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                                                    </svg>
                                                ) : (
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
                                                    </svg>
                                                )}
                                            </div>
                                            <div>
                                                <p className="font-bold text-slate-800 group-hover:text-emerald-700 transition-colors">
                                                    {tx.narration || tx.description || 'Transaction'}
                                                </p>
                                                <p className="text-xs text-slate-500 font-medium">
                                                    {tx.transactionDate || tx.date ? formatDate(tx.transactionDate || tx.date) : 'N/A'}
                                                </p>
                                            </div>
                                        </div>

                                        {tx.reference && (
                                            <p className="text-xs text-slate-400 ml-13">
                                                Ref: {tx.reference}
                                            </p>
                                        )}
                                    </div>

                                    <div className="text-right">
                                        <p className={`text-lg font-bold ${tx.type === 'CREDIT' || tx.amount > 0
                                                ? 'text-green-600'
                                                : 'text-red-600'
                                            }`}>
                                            {tx.type === 'CREDIT' || tx.amount > 0 ? '+' : '-'}
                                            {formatCurrency(Math.abs(tx.amount || tx.currentBalance || 0))}
                                        </p>
                                        {tx.currentBalance !== undefined && (
                                            <p className="text-xs text-slate-500 mt-1 font-medium">
                                                Bal: {formatCurrency(tx.currentBalance)}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!loading && !error && transactions.length === 0 && mobileNumber && (
                <div className="mt-8 p-8 text-center bg-slate-50 rounded-2xl border border-slate-100">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <p className="text-slate-600 font-bold text-lg">No transactions found</p>
                    <p className="text-sm text-slate-500 mt-1">Try adjusting your date range or check the mobile number.</p>
                </div>
            )}
        </div>
    );
}
