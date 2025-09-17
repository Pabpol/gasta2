import { writable, derived } from 'svelte/store';
import type { Expense, Income, Budget } from '../utils/api';
import { expensesApi, incomeApi, budgetApi } from '../utils/api';

// Base stores
export const expenses = writable<Expense[]>([]);
export const income = writable<Income[]>([]);
export const budgets = writable<Budget[]>([]);
export const loading = writable(false);
export const error = writable<string | null>(null);

// Derived stores for computed values
export const currentMonthExpenses = derived(expenses, ($expenses) => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    return $expenses.filter(expense => {
        const expenseDate = new Date(expense.fecha);
        return expenseDate.getMonth() === currentMonth &&
            expenseDate.getFullYear() === currentYear &&
            expense.tipo !== 'transfer_in';
    });
});

export const currentMonthIncome = derived(income, ($income) => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    return $income.filter(inc => {
        const incomeDate = new Date(inc.fecha);
        return incomeDate.getMonth() === currentMonth &&
            incomeDate.getFullYear() === currentYear;
    });
});

export const monthlyTotals = derived(
    [currentMonthExpenses, currentMonthIncome],
    ([$expenses, $income]) => {
        const totalExpenses = $expenses.reduce((sum, exp) => sum + exp.monto_tu_parte, 0);
        const totalIncome = $income.reduce((sum, inc) => sum + inc.monto_clp, 0);
        const balance = totalIncome - totalExpenses;

        return {
            expenses: totalExpenses,
            income: totalIncome,
            balance,
            expenseCount: $expenses.length,
            incomeCount: $income.length
        };
    }
);

export const categoryTotals = derived(currentMonthExpenses, ($expenses) => {
    const categoryMap = new Map<string, number>();

    $expenses.forEach(expense => {
        const current = categoryMap.get(expense.categoria) || 0;
        categoryMap.set(expense.categoria, current + expense.monto_tu_parte);
    });

    return Array.from(categoryMap.entries())
        .map(([categoria, total]) => ({ categoria, total }))
        .sort((a, b) => b.total - a.total);
});

export const budgetStatus = derived(
    [budgets, categoryTotals],
    ([$budgets, $categoryTotals]) => {
        return $budgets.map(budget => {
            const spent = $categoryTotals.find(cat => cat.categoria === budget.categoria)?.total || 0;
            const budgetAmount = Number(budget.presupuesto_mensual) || 0;

            // Ensure valid numbers to avoid NaN
            const safeSpent = Number(spent) || 0;
            const percentage = budgetAmount > 0 ? (safeSpent / budgetAmount) * 100 : 0;
            const safePercentage = isNaN(percentage) ? 0 : percentage;

            return {
                ...budget,
                gastado_actual: safeSpent,
                porcentaje_usado: safePercentage,
                presupuesto_mensual: budgetAmount,
                estado: safePercentage >= 100 ? 'excedido' :
                    safePercentage >= 80 ? 'alerta' : 'ok'
            };
        });
    }
);

// Actions
export const expenseActions = {
    async loadAll() {
        loading.set(true);
        error.set(null);
        try {
            const data = await expensesApi.getAll();
            expenses.set(data);
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error loading expenses');
        } finally {
            loading.set(false);
        }
    },

    async loadByMonth(year: number, month: number) {
        loading.set(true);
        error.set(null);
        try {
            const data = await expensesApi.getByMonth(year, month);
            expenses.set(data);
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error loading expenses');
        } finally {
            loading.set(false);
        }
    },

    async updateCategory(id: string, categoria: string, subcategoria?: string) {
        try {
            await expensesApi.updateCategory(id, categoria, subcategoria);
            // Reload data to reflect changes
            await this.loadAll();
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error updating category');
        }
    }
};

export const incomeActions = {
    async loadAll() {
        loading.set(true);
        error.set(null);
        try {
            const data = await incomeApi.getAll();
            income.set(data);
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error loading income');
        } finally {
            loading.set(false);
        }
    },

    async create(newIncome: { descripcion: string; monto_clp: number; fecha?: string; contraparte?: string }) {
        loading.set(true);
        error.set(null);
        try {
            await incomeApi.create(newIncome);
            // Reload data to include new income
            await this.loadAll();
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error creating income');
            throw err;
        } finally {
            loading.set(false);
        }
    }
};

export const budgetActions = {
    async loadAll() {
        loading.set(true);
        error.set(null);
        try {
            const data = await budgetApi.getAll();
            budgets.set(data);
        } catch (err) {
            console.error('Error loading budgets:', err);
            error.set(err instanceof Error ? err.message : 'Error loading budgets');
        } finally {
            loading.set(false);
        }
    },

    async create(newBudget: { categoria: string; presupuesto_mensual: number }) {
        loading.set(true);
        error.set(null);
        try {
            await budgetApi.upsert(newBudget);
            // Reload data to include new budget
            await this.loadAll();
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error creating budget');
            throw err;
        } finally {
            loading.set(false);
        }
    },

    async delete(categoria: string) {
        loading.set(true);
        error.set(null);
        try {
            await budgetApi.delete(categoria);
            // Reload data to reflect deletion
            await this.loadAll();
        } catch (err) {
            error.set(err instanceof Error ? err.message : 'Error deleting budget');
            throw err;
        } finally {
            loading.set(false);
        }
    }
};

// Initialize data loading
export const initializeStores = async () => {
    await Promise.all([
        expenseActions.loadAll(),
        incomeActions.loadAll(),
        budgetActions.loadAll()
    ]);
};
