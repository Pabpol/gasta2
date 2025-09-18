<script lang="ts">
	import { onMount } from 'svelte';
	import { expenseActions, expenses, loading, error } from '$lib/stores/data';
	import { formatCurrency, formatDate, expensesApi, type Expense } from '$lib/utils/api';
	
	// Filter state
	let filters = {
		categoria: '',
		fechaDesde: '',
		fechaHasta: '',
		montoMin: 0,
		montoMax: 0
	};
	
	let showFilters = false;
	
	// Manual expense form state
	let showAddForm = false;
	let formData = {
		descripcion: '',
		monto_clp: 0,
		fecha: new Date().toISOString().split('T')[0], // Today's date
		medio: 'TC', // Default to credit card
		tipo: 'expense',
		categoria: '' // Add category selection
	};
	
	let formLoading = false;
	let formError: string | null = null;
	let formSuccess: string | null = null;

	// Delete functionality state
	let showDeleteModal = false;
	let expenseToDelete: Expense | null = null;
	let deleteLoading = false;
	let deleteError: string | null = null;

	// Available categories
	const categories = [
		{ value: '', label: '🤖 Categorización Automática' },
		{ value: 'alimentacion', label: '🍽️ Alimentación' },
		{ value: 'transporte', label: '🚗 Transporte' },
		{ value: 'combustible', label: '⛽ Combustible' },
		{ value: 'supermercado', label: '🛒 Supermercado' },
		{ value: 'salud', label: '🏥 Salud' },
		{ value: 'entretenimiento', label: '🎬 Entretenimiento' },
		{ value: 'ropa', label: '👕 Ropa' },
		{ value: 'hogar', label: '🏠 Hogar' },
		{ value: 'educacion', label: '📚 Educación' },
		{ value: 'tecnologia', label: '💻 Tecnología' },
		{ value: 'comercio_electronico', label: '🛍️ Comercio Electrónico' },
		{ value: 'servicios', label: '⚙️ Servicios' },
		{ value: 'restaurantes', label: '🍕 Restaurantes' },
		{ value: 'otros', label: '📦 Otros' }
	];

	// Payment methods
	const paymentMethods = [
		{ value: 'TC', label: '💳 Tarjeta de Crédito' },
		{ value: 'TD', label: '💳 Tarjeta de Débito' },
		{ value: 'Efectivo', label: '💵 Efectivo' },
		{ value: 'Transferencia', label: '🏦 Transferencia' },
		{ value: 'Cheque', label: '📝 Cheque' },
		{ value: 'Otro', label: '❓ Otro' }
	];

	// Expense types
	const expenseTypes = [
		{ value: 'expense', label: '💸 Gasto Personal' },
		{ value: 'transfer_out', label: '🔄 Transferencia Enviada' },
		{ value: 'shared', label: '👥 Gasto Compartido' }
	];
	
	// Computed filtered expenses
	$: filteredExpenses = $expenses.filter(expense => {
		// Category filter
		if (filters.categoria && expense.categoria !== filters.categoria) {
			return false;
		}
		
		// Date range filter
		if (filters.fechaDesde && expense.fecha < filters.fechaDesde) {
			return false;
		}
		if (filters.fechaHasta && expense.fecha > filters.fechaHasta) {
			return false;
		}
		
		// Amount range filter
		if (filters.montoMin > 0 && expense.monto_tu_parte < filters.montoMin) {
			return false;
		}
		if (filters.montoMax > 0 && expense.monto_tu_parte > filters.montoMax) {
			return false;
		}
		
		return true;
	}).sort((a, b) => {
		// Sort by date, most recent first (descending order)
		return new Date(b.fecha).getTime() - new Date(a.fecha).getTime();
	});
	
	// Get unique categories for filter dropdown
	$: availableCategories = [...new Set($expenses.map(expense => expense.categoria))].sort();
	
	// Summary of filtered expenses
	$: summary = {
		total: filteredExpenses.reduce((sum, expense) => sum + expense.monto_tu_parte, 0),
		count: filteredExpenses.length,
		average: filteredExpenses.length > 0 ? 
			filteredExpenses.reduce((sum, expense) => sum + expense.monto_tu_parte, 0) / filteredExpenses.length : 0
	};
	
	// Load expense data on mount
	onMount(() => {
		expenseActions.loadAll();
	});

	// Manual expense form functions
	async function handleSubmit(event: Event) {
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
			await expensesApi.create({
				descripcion: formData.descripcion.trim(),
				monto_clp: formData.monto_clp,
				fecha: formData.fecha + 'T12:00:00', // Add time to avoid timezone issues
				medio: formData.medio,
				tipo: formData.tipo,
				fuente: 'manual',
				categoria: formData.categoria || undefined // Send category if selected
			});

			formSuccess = 'Gasto creado exitosamente';
			
			// Reset form
			formData = {
				descripcion: '',
				monto_clp: 0,
				fecha: new Date().toISOString().split('T')[0],
				medio: 'TC',
				tipo: 'expense',
				categoria: ''
			};
			
			// Reload expenses to show the new one
			expenseActions.loadAll();
			
			// Hide form after successful submission
			showAddForm = false;

		} catch (err) {
			formError = err instanceof Error ? err.message : 'Error al crear el gasto';
		} finally {
			formLoading = false;
		}
	}
	
	function clearFilters() {
		filters = {
			categoria: '',
			fechaDesde: '',
			fechaHasta: '',
			montoMin: 0,
			montoMax: 0
		};
	}

	// Delete functionality functions
	function confirmDelete(expense: Expense) {
		expenseToDelete = expense;
		showDeleteModal = true;
		deleteError = null;
	}

	async function handleDelete() {
		if (!expenseToDelete) return;

		deleteLoading = true;
		deleteError = null;

		try {
			await expensesApi.delete(expenseToDelete.id);

			// Success - reload expenses and close modal
			expenseActions.loadAll();
			showDeleteModal = false;
			expenseToDelete = null;

		} catch (err) {
			deleteError = err instanceof Error ? err.message : 'Error al eliminar el gasto';
		} finally {
			deleteLoading = false;
		}
	}

	function cancelDelete() {
		showDeleteModal = false;
		expenseToDelete = null;
		deleteError = null;
	}
	
	function getCategoryColor(categoria: string): string {
		const colors = {
			'alimentacion': 'bg-green-100 text-green-800',
			'transporte': 'bg-blue-100 text-blue-800',
			'salud': 'bg-red-100 text-red-800',
			'entretenimiento': 'bg-purple-100 text-purple-800',
			'supermercado': 'bg-yellow-100 text-yellow-800',
			'combustible': 'bg-orange-100 text-orange-800',
			'comercio_electronico': 'bg-indigo-100 text-indigo-800',
			'otros': 'bg-gray-100 text-gray-800'
		};
		return colors[categoria] || 'bg-gray-100 text-gray-800';
	}
	
	function getStatusColor(estado: string): string {
		switch (estado) {
			case 'confirmed': return 'bg-green-100 text-green-800';
			case 'pending': return 'bg-yellow-100 text-yellow-800';
			case 'cancelled': return 'bg-red-100 text-red-800';
			default: return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<svelte:head>
	<title>Gastos - Gasta2</title>
</svelte:head>

<div class="px-4 py-6 sm:px-0">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Todos los Gastos</h1>
		<p class="mt-2 text-gray-600">Revisa y filtra tu historial completo de gastos</p>
	</div>

	{#if $error}
		<div class="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
			<div class="flex">
				<div class="text-red-400 text-xl">⚠️</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">Error</h3>
					<div class="mt-2 text-sm text-red-700">{$error}</div>
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

	<!-- Add Expense Form -->
	{#if showAddForm}
		<div class="mb-8 bg-white shadow rounded-lg p-6">
			<div class="flex justify-between items-center mb-6">
				<h2 class="text-lg font-semibold text-gray-900">Nuevo Gasto Manual</h2>
				<button 
					type="button" 
					class="text-gray-400 hover:text-gray-600"
					on:click={() => showAddForm = false}
				>
					✕
				</button>
			</div>

			<form on:submit|preventDefault={handleSubmit} class="space-y-6">
				<!-- Description -->
				<div>
					<label for="descripcion" class="block text-sm font-medium text-gray-700 mb-1">
						Descripción *
					</label>
					<input
						type="text"
						id="descripcion"
						bind:value={formData.descripcion}
						placeholder="Ej: Almuerzo en restaurante, Transferencia a Juan, etc."
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
						placeholder="15000"
						min="1"
						step="1"
						class="input-field"
						required
						disabled={formLoading}
					/>
				</div>

				<!-- Date -->
				<div>
					<label for="fecha" class="block text-sm font-medium text-gray-700 mb-1">
						Fecha *
					</label>
					<input
						type="date"
						id="fecha"
						bind:value={formData.fecha}
						class="input-field"
						required
						disabled={formLoading}
					/>
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

				<!-- Expense Type -->
				<div>
					<label for="tipo" class="block text-sm font-medium text-gray-700 mb-1">
						Tipo de Gasto *
					</label>
					<select
						id="tipo"
						bind:value={formData.tipo}
						class="input-field"
						required
						disabled={formLoading}
					>
						{#each expenseTypes as type}
							<option value={type.value}>{type.label}</option>
						{/each}
					</select>
				</div>

				<!-- Category -->
				<div>
					<label for="categoria" class="block text-sm font-medium text-gray-700 mb-1">
						Categoría
					</label>
					<select
						id="categoria"
						bind:value={formData.categoria}
						class="input-field"
						disabled={formLoading}
					>
						{#each categories as category}
							<option value={category.value}>{category.label}</option>
						{/each}
					</select>
					<p class="mt-1 text-xs text-gray-500">
						Si no seleccionas categoría, el sistema intentará categorizarlo automáticamente
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
							⏳ Guardando...
						{:else}
							💾 Crear Gasto
						{/if}
					</button>
					<button 
						type="button" 
						class="btn btn-secondary" 
						on:click={() => showAddForm = false}
						disabled={formLoading}
					>
						❌ Cancelar
					</button>
				</div>
			</form>
		</div>
	{/if}

	<!-- Controls -->
	<div class="mb-6 flex flex-wrap gap-3">
		<button 
			class="btn btn-primary"
			on:click={() => showAddForm = !showAddForm}
		>
			{#if showAddForm}
				❌ Cancelar
			{:else}
				➕ Agregar Gasto Manual
			{/if}
		</button>
		<button 
			class="btn btn-secondary"
			on:click={() => showFilters = !showFilters}
		>
			🔍 {showFilters ? 'Ocultar' : 'Mostrar'} Filtros
		</button>
		<button 
			class="btn btn-secondary"
			on:click={() => expenseActions.loadAll()}
			disabled={$loading}
		>
			🔄 Actualizar
		</button>
	</div>

	<!-- Filters -->
	{#if showFilters}
		<div class="mb-6 card">
			<div class="card-header">
				<h3 class="text-lg font-medium text-gray-900">Filtros</h3>
			</div>
			<div class="card-body">
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<!-- Category Filter -->
					<div>
						<label for="categoria" class="block text-sm font-medium text-gray-700 mb-1">
							Categoría
						</label>
						<select
							id="categoria"
							bind:value={filters.categoria}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
						>
							<option value="">Todas las categorías</option>
							{#each availableCategories as category}
								<option value={category}>{category}</option>
							{/each}
						</select>
					</div>
					
					<!-- Date From -->
					<div>
						<label for="fechaDesde" class="block text-sm font-medium text-gray-700 mb-1">
							Desde
						</label>
						<input
							type="date"
							id="fechaDesde"
							bind:value={filters.fechaDesde}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
						/>
					</div>
					
					<!-- Date To -->
					<div>
						<label for="fechaHasta" class="block text-sm font-medium text-gray-700 mb-1">
							Hasta
						</label>
						<input
							type="date"
							id="fechaHasta"
							bind:value={filters.fechaHasta}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
						/>
					</div>
					
					<!-- Amount Min -->
					<div>
						<label for="montoMin" class="block text-sm font-medium text-gray-700 mb-1">
							Monto mínimo
						</label>
						<input
							type="number"
							id="montoMin"
							bind:value={filters.montoMin}
							min="0"
							step="1000"
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
							placeholder="0"
						/>
					</div>
					
					<!-- Amount Max -->
					<div>
						<label for="montoMax" class="block text-sm font-medium text-gray-700 mb-1">
							Monto máximo
						</label>
						<input
							type="number"
							id="montoMax"
							bind:value={filters.montoMax}
							min="0"
							step="1000"
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
							placeholder="Sin límite"
						/>
					</div>
					
					<!-- Clear Filters -->
					<div class="flex items-end">
						<button 
							class="btn btn-secondary w-full"
							on:click={clearFilters}
						>
							🗑️ Limpiar Filtros
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Summary -->
	<div class="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
		<div class="card">
			<div class="card-body text-center">
				<div class="text-2xl font-bold text-primary-600">{summary.count}</div>
				<div class="text-sm text-gray-600">Gastos encontrados</div>
			</div>
		</div>
		<div class="card">
			<div class="card-body text-center">
				<div class="text-2xl font-bold text-red-600">{formatCurrency(summary.total)}</div>
				<div class="text-sm text-gray-600">Total filtrado</div>
			</div>
		</div>
		<div class="card">
			<div class="card-body text-center">
				<div class="text-2xl font-bold text-gray-600">{formatCurrency(summary.average)}</div>
				<div class="text-sm text-gray-600">Promedio por gasto</div>
			</div>
		</div>
	</div>

	<!-- Expense List -->
	<div class="card">
		<div class="card-header">
			<h3 class="text-lg font-medium text-gray-900">
				Lista de Gastos
				{#if filters.categoria || filters.fechaDesde || filters.fechaHasta || filters.montoMin > 0 || filters.montoMax > 0}
					<span class="text-sm font-normal text-gray-500">(filtrada)</span>
				{/if}
			</h3>
		</div>
		<div class="card-body">
			{#if $loading && $expenses.length === 0}
				<div class="text-center py-8">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
					<p class="mt-2 text-gray-500">Cargando gastos...</p>
				</div>
			{:else if filteredExpenses.length > 0}
				<div class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Fecha
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Descripción
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Categoría
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Monto
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Estado
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Fuente
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Acciones
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							{#each filteredExpenses as expense (expense.id)}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
										{formatDate(expense.fecha)}
									</td>
									<td class="px-6 py-4 text-sm text-gray-900">
										<div class="max-w-xs truncate" title={expense.descripcion}>
											{expense.descripcion}
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span class={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(expense.categoria)}`}>
											{expense.categoria}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
										{formatCurrency(expense.monto_tu_parte)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span class={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(expense.estado)}`}>
											{expense.estado}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{expense.fuente}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
										<button
											class="text-red-600 hover:text-red-900 transition-colors duration-200"
											on:click={() => confirmDelete(expense)}
											title="Eliminar gasto"
										>
											🗑️
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else if $expenses.length > 0}
				<div class="text-center py-8 text-gray-500">
					<div class="text-4xl mb-2">🔍</div>
					<p>No se encontraron gastos con los filtros aplicados</p>
					<p class="text-sm mt-1">Intenta ajustar los criterios de búsqueda</p>
				</div>
			{:else}
				<div class="text-center py-8 text-gray-500">
					<div class="text-4xl mb-2">📊</div>
					<p>No hay gastos registrados</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Delete Confirmation Modal -->
	{#if showDeleteModal && expenseToDelete}
		<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" on:click={cancelDelete}>
			<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" on:click|stopPropagation>
				<div class="mt-3">
					<div class="flex items-center justify-center">
						<div class="text-red-500 text-4xl">⚠️</div>
					</div>
					<h3 class="text-lg font-medium text-gray-900 text-center mt-4">
						¿Eliminar gasto?
					</h3>
					<div class="mt-4 px-4">
						<p class="text-sm text-gray-500 text-center">
							¿Estás seguro de que quieres eliminar este gasto?
						</p>
						<div class="mt-4 bg-gray-50 rounded-md p-3">
							<div class="text-sm">
								<p><strong>Descripción:</strong> {expenseToDelete.descripcion}</p>
								<p><strong>Monto:</strong> {formatCurrency(expenseToDelete.monto_tu_parte)}</p>
								<p><strong>Fecha:</strong> {formatDate(expenseToDelete.fecha)}</p>
								<p><strong>Categoría:</strong> {expenseToDelete.categoria}</p>
							</div>
						</div>
					</div>

					{#if deleteError}
						<div class="mt-4 bg-red-50 border border-red-200 rounded-md p-3">
							<div class="flex">
								<div class="text-red-400 text-sm">⚠️</div>
								<div class="ml-2">
									<p class="text-sm text-red-700">{deleteError}</p>
								</div>
							</div>
						</div>
					{/if}

					<div class="flex space-x-3 mt-6">
						<button
							type="button"
							class="flex-1 btn btn-secondary"
							on:click={cancelDelete}
							disabled={deleteLoading}
						>
							❌ Cancelar
						</button>
						<button
							type="button"
							class="flex-1 btn bg-red-600 hover:bg-red-700 text-white"
							on:click={handleDelete}
							disabled={deleteLoading}
						>
							{#if deleteLoading}
								⏳ Eliminando...
							{:else}
								🗑️ Eliminar
							{/if}
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
