<script lang="ts">
	import { onMount } from 'svelte';
	import Chart from '$lib/components/Chart.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import { dashboardApi } from '$lib/utils/api';

	// Local state for dashboard data
	let dashboardData = {
		total_expenses: 0,
		total_income: 0,
		balance: 0,
		expense_count: 0,
		income_count: 0,
		period_info: {
			period_name: '',
			pay_day: 25,
			days_until_pay: 0,
			next_pay_date: ''
		}
	};
	let categoryData: any[] = [];
	let monthlyTrendData: any[] = [];
	let loading = true;
	let error: string | null = null;

	// Reactive updates for chart data
	$: categoryChartData = categoryData.map(cat => ({
		categoria: cat.categoria,
		total: cat.total
	}));

	$: monthlyTrendChartData = monthlyTrendData.map(trend => {
		// Format month for better display (e.g., "2025-09" -> "Sep 2025")
		const monthStr = trend.month;
		const [year, month] = monthStr.split('-');
		const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
		                   'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
		const formattedMonth = `${monthNames[parseInt(month) - 1]} ${year}`;
		
		return {
			month: formattedMonth,
			expenses: Number(trend.expenses) || 0,
			balance: Number(trend.balance) || 0  // Use balance instead of income
		};
	});

	async function loadDashboardData() {
		loading = true;
		error = null;
		
		try {
			// Load summary data
			const summaryResponse = await dashboardApi.getSummary();
			dashboardData = summaryResponse;
			
			// Load category breakdown data
			try {
				const categoryResponse = await dashboardApi.getCategoryBreakdown();
				categoryData = categoryResponse || [];
			} catch (categoryErr) {
				console.warn('Category data not available:', categoryErr);
				categoryData = [];
			}
			
			// Load monthly trends data
			try {
				const trendsResponse = await dashboardApi.getMonthlyTrends(6);
				monthlyTrendData = trendsResponse || [];
			} catch (trendsErr) {
				console.warn('Trends data not available:', trendsErr);
				monthlyTrendData = [];
			}
			
		} catch (err) {
			console.error('Error loading dashboard data:', err);
			error = 'No se pudieron cargar los datos del dashboard. Verifica que el backend esté funcionando.';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadDashboardData();
	});
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="text-center">
		<h1 class="text-3xl font-bold text-gray-900">Dashboard Financiero</h1>
		<p class="mt-2 text-lg text-gray-600">
			{#if dashboardData.period_info?.period_name}
				Resumen del período: {dashboardData.period_info.period_name}
			{:else}
				Resumen de tus gastos e ingresos del período
			{/if}
		</p>
		{#if dashboardData.period_info?.days_until_pay > 0}
			<p class="mt-1 text-sm text-gray-500">
				Próximo pago en {dashboardData.period_info?.days_until_pay || 0} días (día {dashboardData.period_info?.pay_day || 25})
			</p>
		{/if}
	</div>

	{#if error}
		<div class="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
			<div class="flex">
				<div class="text-red-400 text-xl">⚠️</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error al cargar datos</h3>
					<div class="mt-2 text-sm text-red-700">{error}</div>
				</div>
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="text-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
			<p class="mt-2 text-gray-500">Cargando dashboard...</p>
		</div>
	{:else}
		<!-- Stats Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			<StatCard 
				title="Balance Total" 
				value={dashboardData?.balance || 0} 
				icon="💰"
				variant={(dashboardData?.balance || 0) >= 0 ? "success" : "danger"}
				type="currency"
			/>
			<StatCard 
				title="Gastos del Período" 
				value={dashboardData?.total_expenses || 0} 
				icon="📉"
				variant="default"
				type="currency"
			/>
			<StatCard 
				title="Ingresos del Período" 
				value={dashboardData?.total_income || 0} 
				icon="📈"
				variant="success"
				type="currency"
			/>
			<StatCard 
				title="Total Transacciones" 
				value={(dashboardData?.expense_count || 0) + (dashboardData?.income_count || 0)} 
				icon="📊"
				variant="default"
				type="number"
			/>
			<StatCard 
				title="Días hasta próximo pago" 
				value={dashboardData.period_info?.days_until_pay || 0} 
				icon="📅"
				variant={(dashboardData.period_info?.days_until_pay || 0) <= 3 ? "warning" : "default"}
				type="number"
			/>
		</div>

		<!-- Charts -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<!-- Category Breakdown Chart -->
			<div class="bg-white p-6 rounded-lg shadow">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">Gastos por Categoría</h2>
				{#if categoryData.length > 0}
					<Chart 
						type="doughnut" 
						data={categoryChartData}
						height={300}
					/>
				{:else}
					<div class="text-center py-8 text-gray-500">
						<p>No hay datos de categorías disponibles</p>
						<p class="text-sm mt-1">Agrega algunos gastos para ver el desglose por categorías</p>
					</div>
				{/if}
			</div>

			<!-- Monthly Trend Chart -->
			<div class="bg-white p-6 rounded-lg shadow">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">Tendencia Mensual</h2>
				{#if monthlyTrendData.length > 0}
					<Chart 
						type="line" 
						data={monthlyTrendChartData}
						height={300}
					/>
					{#if monthlyTrendData.length === 6 && monthlyTrendData.some(d => d.month === '2025-09')}
						<p class="text-xs text-gray-500 mt-2">
							📊 Datos reales disponibles para algunos meses. Datos anteriores pueden incluir estimaciones para demostración.
						</p>
					{/if}
				{:else}
					<div class="text-center py-8 text-gray-500">
						<p>Datos de tendencia no disponibles</p>
						<p class="text-sm mt-1">Agrega gastos de varios meses para ver la tendencia</p>
					</div>
				{/if}
			</div>
		</div>

		<!-- Quick Actions -->
		<div class="bg-white p-6 rounded-lg shadow">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">Acciones Rápidas</h2>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<a 
					href="/gastos" 
					class="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
				>
					<div class="text-2xl mr-3">📝</div>
					<div>
						<h3 class="font-medium text-gray-900">Ver Gastos</h3>
						<p class="text-sm text-gray-500">Revisar y gestionar gastos</p>
					</div>
				</a>
				<a 
					href="/ingresos" 
					class="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
				>
					<div class="text-2xl mr-3">💰</div>
					<div>
						<h3 class="font-medium text-gray-900">Ver Ingresos</h3>
						<p class="text-sm text-gray-500">Revisar y gestionar ingresos</p>
					</div>
				</a>
				<a 
					href="/presupuestos" 
					class="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
				>
					<div class="text-2xl mr-3">🎯</div>
					<div>
						<h3 class="font-medium text-gray-900">Presupuestos</h3>
						<p class="text-sm text-gray-500">Configurar metas de gasto</p>
					</div>
				</a>
			</div>
		</div>
	{/if}
</div>
