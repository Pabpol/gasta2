import axios from 'axios';

// API configuration
// In production (served from FastAPI), use relative URLs
// In development, use localhost:8000
const API_BASE_URL = (() => {
    // Check if we're in browser environment
    if (typeof window !== 'undefined') {
        // In browser, check if we're on Vite dev server
        if (window.location.port === '5173') {
            return 'http://localhost:8000';  // Development: Vite dev server (browser to host)
        } else {
            return '';  // Production: same domain (FastAPI)
        }
    } else {
        // In SSR environment (server-side), use Docker service name
        return 'http://backend:8000';
    }
})();

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface Expense {
    id: string;
    fecha: string;
    descripcion: string;
    monto_clp: number;
    categoria: string;
    subcategoria?: string;
    medio: string;
    estado: string;
    tipo: string;
    monto_tu_parte: number;
    fuente: string;
}

export interface Income {
    id: string;
    fecha: string;
    descripcion: string;
    monto_clp: number;
    categoria: string;
    tipo: string;
    fuente: string;
}

export interface PeriodInfo {
    period_name: string;
    pay_day: number;
    days_until_pay: number;
    next_pay_date: string;
}

export interface DashboardSummary {
    total_expenses: number;
    total_income: number;
    balance: number;
    expense_count: number;
    income_count: number;
    period_info: PeriodInfo;
}

export interface Budget {
    categoria: string;
    presupuesto_mensual: number;
    gastado_actual: number;
    porcentaje_usado: number;
}

export interface CreateIncomeRequest {
    descripcion: string;
    monto_clp: number;
    fecha?: string;
    contraparte?: string;
}

export interface CreateBudgetRequest {
    categoria: string;
    presupuesto_mensual: number;
}

// Recurring Expenses Types
export interface RecurringExpense {
    id: string;
    descripcion: string;
    monto_clp: number;
    categoria: string;
    medio: string;
    is_recurring: boolean;
    recurring_frequency: string;
    recurring_day: number;
    recurring_end_date?: string;
    recurring_next_date: string;
    fecha: string;
    fuente: string;
    estado: string;
}

export interface CreateRecurringExpenseRequest {
    descripcion: string;
    monto_clp: number;
    categoria: string;
    medio: string;
    recurring_frequency: string;
    recurring_day: number;
    recurring_end_date?: string;
}

export interface UpdateRecurringExpenseRequest {
    descripcion?: string;
    monto_clp?: number;
    categoria?: string;
    medio?: string;
    recurring_frequency?: string;
    recurring_day?: number;
    recurring_end_date?: string;
}

// Installment Purchases Types
export interface InstallmentPurchase {
    id: string;
    descripcion: string;
    is_installment: boolean;
    installment_total_amount: number;
    installment_total_installments: number;
    installment_paid_installments: number;
    installment_installment_amount: number;
    installment_interest_rate: number;
    installment_first_payment_date: string;
    installment_payment_frequency: string;
    installment_remaining_balance: number;
    categoria: string;
    medio: string;
    fecha: string;
    fuente: string;
    estado: string;
}

export interface CreateInstallmentPurchaseRequest {
    descripcion: string;
    installment_total_amount: number;
    installment_total_installments: number;
    categoria: string;
    medio: string;
    installment_interest_rate?: number;
    installment_first_payment_date: string;
    installment_payment_frequency: string;
}

export interface InstallmentPaymentRecordRequest {
    purchase_id: string;
    payment_amount: number;
    payment_date?: string;
}

export interface UpdateInstallmentPurchaseRequest {
    descripcion?: string;
    installment_total_amount?: number;
    installment_total_installments?: number;
    categoria?: string;
    medio?: string;
    installment_interest_rate?: number;
    installment_first_payment_date?: string;
    installment_payment_frequency?: string;
}

export interface UpcomingInstallmentPayment {
    purchase_id: string;
    descripcion: string;
    next_payment_date: string;
    days_until_due: number;
    installment_amount: number;
    installment_number: number;
    total_installments: number;
    remaining_balance: number;
}

export interface InstallmentPurchaseSummary {
    total_debt: number;
    total_purchases: number;
    active_purchases: number;
    monthly_commitment: number;
    upcoming_payments: UpcomingInstallmentPayment[];
}

// API functions
export const expensesApi = {
    // Get all expenses
    getAll: async (): Promise<Expense[]> => {
        const response = await api.get('/api/gastos');
        return response.data;
    },

    // Get expenses by month
    getByMonth: async (year: number, month: number): Promise<Expense[]> => {
        const response = await api.get(`/api/gastos/month/${year}/${month}`);
        return response.data;
    },

    // Create new expense
    create: async (expense: {
        descripcion: string;
        monto_clp: number;
        fecha?: string;
        medio: string;
        tipo: string;
        fuente: string;
        categoria?: string;
    }) => {
        const response = await api.post('/api/gasto', expense);
        return response.data;
    },

    // Update category
    updateCategory: async (id: string, categoria: string, subcategoria?: string) => {
        const response = await api.put(`/api/gasto/${id}/categoria`, {
            gasto_id: id,
            categoria,
            subcategoria: subcategoria || ''
        });
        return response.data;
    },

    // Delete expense
    delete: async (id: string) => {
        const response = await api.delete(`/api/gasto/${id}`);
        return response.data;
    },
};

export const incomeApi = {
    // Create income
    create: async (income: CreateIncomeRequest): Promise<Income> => {
        const response = await api.post('/api/ingreso', income);
        return response.data;
    },

    // Get all income
    getAll: async (): Promise<Income[]> => {
        const response = await api.get('/api/ingresos');
        return response.data;
    },
};

export const budgetApi = {
    // Get all budgets
    getAll: async (): Promise<Budget[]> => {
        const response = await api.get('/api/presupuestos');
        return response.data;
    },

    // Create or update budget
    upsert: async (budget: CreateBudgetRequest): Promise<Budget> => {
        const response = await api.post('/api/presupuesto', budget);
        return response.data;
    },

    // Delete budget
    delete: async (categoria: string): Promise<void> => {
        await api.delete(`/api/presupuesto/${categoria}`);
    },
};

export const recurringExpensesApi = {
    // Get all recurring expenses
    getAll: async (): Promise<RecurringExpense[]> => {
        const response = await api.get('/api/recurring-expenses');
        return response.data.recurring_expenses || [];
    },

    // Create recurring expense
    create: async (recurringExpense: CreateRecurringExpenseRequest): Promise<RecurringExpense> => {
        const response = await api.post('/api/recurring-expenses', recurringExpense);
        return response.data.recurring_expense;
    },

    // Update recurring expense
    update: async (id: string, updates: UpdateRecurringExpenseRequest): Promise<RecurringExpense> => {
        const response = await api.put(`/api/recurring-expenses/${id}`, updates);
        return response.data.recurring_expense;
    },

    // Delete recurring expense
    delete: async (id: string): Promise<void> => {
        await api.delete(`/api/recurring-expenses/${id}`);
    },

    // Generate recurring expenses manually
    generate: async (): Promise<{ generated_count: number }> => {
        const response = await api.post('/api/recurring-expenses/generate');
        return response.data;
    },
};

export const installmentPurchasesApi = {
    // Get all installment purchases
    getAll: async (): Promise<InstallmentPurchase[]> => {
        const response = await api.get('/api/installment-purchases');
        return response.data.installment_purchases || [];
    },

    // Create installment purchase
    create: async (purchase: CreateInstallmentPurchaseRequest): Promise<InstallmentPurchase> => {
        const response = await api.post('/api/installment-purchases', purchase);
        return response.data.installment_purchase;
    },

    // Update installment purchase
    update: async (id: string, updates: UpdateInstallmentPurchaseRequest): Promise<InstallmentPurchase> => {
        const response = await api.put(`/api/installment-purchases/${id}`, updates);
        return response.data.installment_purchase;
    },

    // Delete installment purchase
    delete: async (id: string): Promise<void> => {
        await api.delete(`/api/installment-purchases/${id}`);
    },

    // Record payment
    recordPayment: async (payment: InstallmentPaymentRecordRequest): Promise<{ payment_amount: number }> => {
        const response = await api.post(`/api/installment-purchases/${payment.purchase_id}/payments`, payment);
        return response.data;
    },

    // Get upcoming payments
    getUpcoming: async (daysAhead: number = 30): Promise<UpcomingInstallmentPayment[]> => {
        const response = await api.get(`/api/installment-purchases/upcoming?days_ahead=${daysAhead}`);
        return response.data.upcoming_payments || [];
    },

    // Get summary
    getSummary: async (): Promise<InstallmentPurchaseSummary> => {
        const response = await api.get('/api/installment-purchases/summary');
        return response.data.summary;
    },
};

export const dashboardApi = {
    // Get dashboard summary
    getSummary: async (): Promise<DashboardSummary> => {
        const response = await api.get('/api/dashboard/summary');
        return response.data;
    },

    // Get monthly trends
    getMonthlyTrends: async (months: number = 6) => {
        const response = await api.get(`/api/dashboard/trends?months=${months}`);
        return response.data;
    },

    // Get category breakdown
    getCategoryBreakdown: async (year?: number, month?: number) => {
        const params = new URLSearchParams();
        if (year) params.append('year', year.toString());
        if (month) params.append('month', month.toString());

        const response = await api.get(`/api/dashboard/categories?${params}`);
        return response.data;
    },

    // Get period configuration
    getPeriodConfig: async () => {
        const response = await api.get('/api/config/period');
        return response.data;
    },

    // Update period configuration
    updatePeriodConfig: async (config: { pay_day: number }) => {
        const response = await api.put('/api/config/period', config);
        return response.data;
    },
};

// Helper function to format currency
export const formatCurrency = (amount: number): string => {
    // Handle invalid numbers
    if (!amount || isNaN(amount) || !isFinite(amount)) {
        return '$0';
    }

    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0,
    }).format(amount);
};

// Helper function to format dates
export const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-CL', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
};

export default api;
