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
