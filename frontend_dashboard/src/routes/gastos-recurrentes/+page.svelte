<script lang="ts">
	import { onMount } from 'svelte';
	import { recurringExpensesApi, type RecurringExpense, type CreateRecurringExpenseRequest } from '$lib/utils/api';
	import { formatCurrency, formatDate } from '$lib/utils/api';

	// State management
	let recurringExpenses: RecurringExpense[] = [];
	let loading = true;
	let error: string | null = null;

	// Form state
	let showCreateForm = false;
	let formLoading = false;
	let formError: string | null = null;
	let formSuccess: string | null = null;

	let formData: CreateRecurringExpenseRequest = {
		descripcion: '',
		monto_clp: 0,
		categoria: 'servicios',
		medio: 'TC',
		recurring_frequency: 'monthly',
		recurring_day: 1
	};

	// Available options
	const categories = [
		{ value: 'servicios', label: '⚙️ Servicios' },
		{ value: 'transporte', label: '🚗 Transporte' },
		{ value: 'alimentacion', label: '🍽️ Alimentación' },
		{ value: 'hogar', label: '🏠 Hogar' },
		{ value: 'salud', label: '🏥 Salud' },
		{ value: 'educacion', label: '📚 Educación' },
		{ value: 'entretenimiento', label: '🎬 Entretenimiento' },
		{ value: 'otros', label: '📦 Otros' }
	];

	const paymentMethods = [
		{ value: 'TC', label: '💳 Tarjeta de Crédito' },
		{ value: 'TD', label: '💳 Tarjeta de Débito' },
		{ value: 'Efectivo', label: '💵 Efectivo' },
		{ value: 'Transferencia', label: '🏦 Transferencia' }
	];

	const frequencies = [
		{ value: 'daily', label: '📅 Diario' },
		{ value: 'weekly', label: '📆 Semanal' },
		{ value: 'monthly', label: '📊 Mensual' }
	];

	// Load recurring expenses on mount
	onMount(async () => {
		await loadRecurringExpenses();
	});

	async function loadRecurringExpenses() {
		try {
			loading = true;
			error = null;
			recurringExpenses = await recurringExpensesApi.getAll();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error al cargar gastos recurrentes';
		} finally {
			loading = false;
		}
	}

	async function handleCreate(event: Event) {
		event.preventDefault();

		if (!formData.descripcion.trim()) {
			formError = 'La descripción es requerida';
			return;
		}

		if (formData.monto_clp <= 0) {
			formError = 'El monto debe ser mayor a 0';
			return;
		}

		formLoading = true;
		formError = null;
		formSuccess = null;

		try {
			await recurringExpensesApi.create(formData);

			formSuccess = 'Gasto recurrente creado exitosamente';

			// Reset form
			formData = {
				descripcion: '',
				monto_clp: 0,
				categoria: 'servicios',
				medio: 'TC',
				recurring_frequency: 'monthly',
				recurring_day: 1
			};

			// Reload list
			await loadRecurringExpenses();

			// Hide form after success
			showCreateForm = false;

		} catch (err) {
			formError = err instanceof Error ? err.message : 'Error al crear gasto recurrente';
		} finally {
			formLoading = false;
		}
	}

	async function handleDelete(id: string, descripcion: string) {
		if (!confirm(`¿Estás seguro de que quieres eliminar "${descripcion}"?`)) {
			return;
		}

		try {
			await recurringExpensesApi.delete(id);
			await loadRecurringExpenses();
		} catch (err) {
			alert(`Error al eliminar: ${err instanceof Error ? err.message : 'Error desconocido'}`);
		}
	}

	async function handleGenerateExpenses() {
		try {
			const result = await recurringExpensesApi.generate();
			alert(`Se generaron ${result.generated_count} gastos recurrentes`);
			await loadRecurringExpenses();
		} catch (err) {
			alert(`Error al generar gastos: ${err instanceof Error ? err.message : 'Error desconocido'}`);
		}
	}

	function getFrequencyLabel(frequency: string): string {
		const labels = {
			'daily': 'Diario',
			'weekly': 'Semanal',
			'monthly': 'Mensual'
		};
		return labels[frequency] || frequency;
	}

	function getCategoryColor(categoria: string): string {
		const colors = {
			'servicios': 'bg-blue-100 text-blue-800',
			'transporte': 'bg-green-100 text-green-800',
			'alimentacion': 'bg-orange-100 text-orange-800',
			'hogar': 'bg-purple-100 text-purple-800',
			'salud': 'bg-red-100 text-red-800',
			'otros': 'bg-gray-100 text-gray-800'
		};
		return colors[categoria] || 'bg-gray-100 text-gray-800';
	}
</script>

<svelte:head>
	<title>Gastos Recurrentes - Gasta2</title>
</svelte:head>

<div class="px-4 py-6 sm:px-0">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Gastos Recurrentes</h1>
		<p class="mt-2 text-gray-600">Gestiona tus gastos que se repiten periódicamente</p>
	</div>

	{#if error}
		<div class="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
			<div class="flex">
				<div class="text-red-400 text-xl">⚠️</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error</h3>
					<div class="mt-2 text-sm text-red-700">{error}</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Success/Error Messages for Form -->
	{#if formSuccess}
		<div class="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
			<div class="flex">
				<div class="text-green-400 text-xl">✅</div>
				<div class="ml-3">
					<div class="text-sm text-green-700">{formSuccess}</div>
				</div>
			</div>
		</div>
	{/if}

	{#if formError}
		<div class="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
			<div class="flex">
				<div class="text-red-400 text-xl">⚠️</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error en formulario</h3>
					<div class="mt-2 text-sm text-red-700">{formError}</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Controls -->
	<div class="mb-6 flex flex-wrap gap-3">
		<button
			class="btn btn-primary"
			on:click={() => showCreateForm = !showCreateForm}
		>
			{#if showCreateForm}
				❌ Cancelar
			{:else}
				➕ Nuevo Gasto Recurrente
			{/if}
		</button>
		<button
			class="btn btn-secondary"
			on:click={handleGenerateExpenses}
		>
			🔄 Generar Gastos Pendientes
		</button>
		<button
			class="btn btn-secondary"
			on:click={loadRecurringExpenses}
			disabled={loading}
		>
			🔄 Actualizar
		</button>
	</div>

	<!-- Create Form -->
	{#if showCreateForm}
		<div class="mb-8 bg-white shadow rounded-lg p-6">
			<div class="flex justify-between items-center mb-6">
				<h2 class="text-lg font-semibold text-gray-900">Nuevo Gasto Recurrente</h2>
				<button
					type="button"
					class="text-gray-400 hover:text-gray-600"
					on:click={() => showCreateForm = false}
				>
					✕
				</button>
			</div>

			<form on:submit|preventDefault={handleCreate} class="space-y-6">
				<!-- Description -->
				<div>
					<label for="descripcion" class="block text-sm font-medium text-gray-700 mb-1">
						Descripción *
					</label>
					<input
						type="text"
						id="descripcion"
						bind:value={formData.descripcion}
						placeholder="Ej: Arriendo departamento, Seguro de auto, etc."
						class="input-field"
						required
						disabled={formLoading}
					/>
				</div>

				<!-- Amount -->
				<div>
					<label for="monto" class="block text-sm font-medium text-gray-700 mb-1">
						Monto (CLP) *
					</label>
					<input
						type="number"
						id="monto"
						bind:value={formData.monto_clp}
						placeholder="150000"
						min="1"
						class="input-field"
						required
						disabled={formLoading}
					/>
				</div>

				<!-- Category -->
				<div>
					<label for="categoria" class="block text-sm font-medium text-gray-700 mb-1">
						Categoría *
					</label>
					<select
						id="categoria"
						bind:value={formData.categoria}
						class="input-field"
						required
						disabled={formLoading}
					>
						{#each categories as category}
							<option value={category.value}>{category.label}</option>
						{/each}
					</select>
				</div>

				<!-- Payment Method -->
				<div>
					<label for="medio" class="block text-sm font-medium text-gray-700 mb-1">
						Medio de Pago *
					</label>
					<select
						id="medio"
						bind:value={formData.medio}
						class="input-field"
						required
						disabled={formLoading}
					>
						{#each paymentMethods as method}
							<option value={method.value}>{method.label}</option>
						{/each}
					</select>
				</div>

				<!-- Frequency -->
				<div>
					<label for="frequency" class="block text-sm font-medium text-gray-700 mb-1">
						Frecuencia *
					</label>
					<select
						id="frequency"
						bind:value={formData.recurring_frequency}
						class="input-field"
						required
						disabled={formLoading}
					>
						{#each frequencies as freq}
							<option value={freq.value}>{freq.label}</option>
						{/each}
					</select>
				</div>

				<!-- Day -->
				<div>
					<label for="day" class="block text-sm font-medium text-gray-700 mb-1">
						Día del mes/semana *
					</label>
					<input
						type="number"
						id="day"
						bind:value={formData.recurring_day}
						min="1"
						max="31"
						class="input-field"
						required
						disabled={formLoading}
					/>
					<p class="mt-1 text-xs text-gray-500">
						Para frecuencia mensual: día del mes (1-31)<br>
						Para frecuencia semanal: día de la semana (1=Lunes, 7=Domingo)
					</p>
				</div>

				<!-- Submit Buttons -->
				<div class="flex space-x-3">
					<button
						type="submit"
						class="btn btn-primary"
						disabled={formLoading}
					>
						{#if formLoading}
							⏳ Creando...
						{:else}
							💾 Crear Gasto Recurrente
						{/if}
					</button>
					<button
						type="button"
						class="btn btn-secondary"
						on:click={() => showCreateForm = false}
						disabled={formLoading}
					>
						❌ Cancelar
					</button>
				</div>
			</form>
		</div>
	{/if}

	<!-- Recurring Expenses List -->
	<div class="card">
		<div class="card-header">
			<h3 class="text-lg font-medium text-gray-900">Gastos Recurrentes</h3>
		</div>
		<div class="card-body">
			{#if loading}
				<div class="text-center py-8">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
					<p class="mt-2 text-gray-500">Cargando gastos recurrentes...</p>
				</div>
			{:else if recurringExpenses.length > 0}
				<div class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Descripción
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Monto
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Categoría
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Frecuencia
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Próximo
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Acciones
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							{#each recurringExpenses as expense (expense.id)}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
										{expense.descripcion}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
										{formatCurrency(expense.monto_clp)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span class={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(expense.categoria)}`}>
											{expense.categoria}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{getFrequencyLabel(expense.recurring_frequency)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{formatDate(expense.recurring_next_date)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
										<button
											class="text-red-600 hover:text-red-900 transition-colors duration-200"
											on:click={() => handleDelete(expense.id, expense.descripcion)}
											title="Eliminar gasto recurrente"
										>
											🗑️
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="text-center py-8 text-gray-500">
					<div class="text-4xl mb-2">🔄</div>
					<p>No tienes gastos recurrentes configurados</p>
					<p class="text-sm mt-1">Crea tu primer gasto recurrente para automatizar tus finanzas</p>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.input-field {
		@apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500;
	}

	.btn {
		@apply px-4 py-2 rounded-md font-medium transition-colors duration-200;
	}

	.btn-primary {
		@apply bg-primary-600 text-white hover:bg-primary-700;
	}

	.btn-secondary {
		@apply bg-gray-200 text-gray-700 hover:bg-gray-300;
	}

	.card {
		@apply bg-white shadow rounded-lg overflow-hidden;
	}

	.card-header {
		@apply px-6 py-4 bg-gray-50 border-b border-gray-200;
	}

	.card-body {
		@apply px-6 py-4;
	}
</style>