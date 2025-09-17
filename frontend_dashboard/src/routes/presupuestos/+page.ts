import { budgetActions, expenseActions } from '$lib/stores/data';

export async function load() {
    // Load data both in SSR and client
    try {
        await Promise.all([
            budgetActions.loadAll(),
            expenseActions.loadAll()
        ]);
    } catch (err) {
        console.error('Page load function error:', err);
    }

    return {};
}
