<script lang="ts">
	import { budgets, budgetStatus, budgetActions, loading, error } from '$lib/stores/data';
	import { formatCurrency } from '$lib/utils/api';
	
	// Debug reactive stores
	// $: {
	// 	console.log('Store debug:');
	// 	console.log('- Budgets count:', $budgets.length);
	// 	console.log('- Budget status count:', $budgetStatus.length);
	// 	console.log('- Loading:', $loading);
	// 	console.log('- Error:', $error);
	// 	if ($budgets.length > 0) {
	// 		console.log('- First budget:', $budgets[0]);
	// 	}
	// 	if ($budgetStatus.length > 0) {
	// 		console.log('- First budget status:', $budgetStatus[0]);
	// 	}
	// }
	
	// Form state
	let formData = {
		categoria: '',
		presupuesto_mensual: 0
	};
	
	let editingBudget: string | null = null; // Para saber cuál presupuesto estamos editando
	let showForm = false;
	let formErrors: Record<string, string> = {};
	
	// Available categories (you might want to fetch this from the backend)
	const availableCategories = [
		'alimentacion',
		'transporte',
		'combustible',
		'supermercado',
		'salud',
		'entretenimiento',
		'ropa',
		'hogar',
		'educacion',
		'tecnologia',
		'comercio_electronico',
		'servicios',
		'restaurantes',
		'otros'
	];
	
	// Simple reactive debug
	// $: {
	// 	console.log('Store debug:');
	// 	console.log('- Budgets count:', $budgets.length);
	// 	console.log('- Budget status count:', $budgetStatus.length);
	// 	console.log('- Loading:', $loading);
	// 	console.log('- Error:', $error);
	// 	if ($budgets.length > 0) {
	// 		console.log('- First budget:', $budgets[0]);
	// 	}
	// 	if ($budgetStatus.length > 0) {
	// 		console.log('- First budget status:', $budgetStatus[0]);
	// 	}
	// }
	
	async function handleSubmit(event: Event) {
		event.preventDefault();
		
		// Reset errors
		formErrors = {};
		
		// Validation
		if (!formData.categoria) {
			formErrors.categoria = 'La categoría es requerida';
		}
		if (formData.presupuesto_mensual <= 0) {
			formErrors.presupuesto_mensual = 'El presupuesto debe ser mayor a 0';
		}
		
		// Check if category already has a budget (only when creating, not editing)
		if (!editingBudget && $budgets.some(budget => budget.categoria === formData.categoria)) {
			formErrors.categoria = 'Esta categoría ya tiene un presupuesto configurado';
		}
		
		// If there are errors, don't submit
		if (Object.keys(formErrors).length > 0) {
			return;
		}
		
		try {
			if (editingBudget) {
				// Editing existing budget
				await budgetActions.create({
					categoria: formData.categoria,
					presupuesto_mensual: formData.presupuesto_mensual
				});
			} else {
				// Creating new budget
				await budgetActions.create({
					categoria: formData.categoria,
					presupuesto_mensual: formData.presupuesto_mensual
				});
			}
			
			// Reset form on success
			cancelForm();
		} catch (err) {
			// Error is handled by the store
			console.error('Error saving budget:', err);
		}
	}
	
	function startEdit(budget: any) {
		editingBudget = budget.categoria;
		formData = {
			categoria: budget.categoria,
			presupuesto_mensual: budget.presupuesto_mensual
		};
		formErrors = {};
		showForm = true;
	}
	
	async function deleteBudget(categoria: string) {
		if (confirm(`¿Estás seguro de que quieres eliminar el presupuesto de "${categoria}"?`)) {
			try {
				await budgetActions.delete(categoria);
			} catch (err) {
				console.error('Error deleting budget:', err);
			}
		}
	}
	
	function cancelForm() {
		formData = {
			categoria: '',
			presupuesto_mensual: 0
		};
		formErrors = {};
		editingBudget = null;
		showForm = false;
	}
	
	function getStatusColor(estado: string): string {
		switch (estado) {
			case 'ok': return 'text-green-600 bg-green-100';
			case 'alerta': return 'text-yellow-600 bg-yellow-100';
			case 'excedido': return 'text-red-600 bg-red-100';
			default: return 'text-gray-600 bg-gray-100';
		}
	}
	
	function getStatusIcon(estado: string): string {
		switch (estado) {
			case 'ok': return '✅';
			case 'alerta': return '⚠️';
			case 'excedido': return '🚨';
			default: return '📊';
		}
	}
	
	function getProgressBarColor(porcentaje: number): string {
		if (porcentaje >= 100) return 'bg-red-500';
		if (porcentaje >= 80) return 'bg-yellow-500';
		return 'bg-green-500';
	}
</script>

<svelte:head>
	<title>Presupuestos - Gasta2</title>
</svelte:head>

<div class="px-4 py-6 sm:px-0">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Gestión de Presupuestos</h1>
		<p class="mt-2 text-gray-600">Define y monitorea tus límites de gasto por categoría</p>
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

	<!-- Add Budget Button -->
	{#if !showForm}
		<div class="mb-6">
			<button 
				class="btn btn-primary" 
				on:click={() => showForm = true}
			>
				🎯 Crear Presupuesto
			</button>
		</div>
	{/if}

	<!-- Add Budget Form -->
	{#if showForm}
		<div class="mb-8 card">
			<div class="card-header">
				<h3 class="text-lg font-medium text-gray-900">
					{editingBudget ? 'Editar Presupuesto' : 'Nuevo Presupuesto'}
				</h3>
			</div>
			<div class="card-body">
				<form on:submit={handleSubmit} class="space-y-4">
					<!-- Category -->
					<div>
						<label for="categoria" class="block text-sm font-medium text-gray-700 mb-1">
							Categoría *
						</label>
						<select
							id="categoria"
							bind:value={formData.categoria}
							disabled={editingBudget !== null}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
							class:border-red-300={formErrors.categoria}
						>
							<option value="">Selecciona una categoría</option>
							{#each availableCategories as category}
								<option value={category}>{category}</option>
							{/each}
						</select>
						{#if formErrors.categoria}
							<p class="mt-1 text-sm text-red-600">{formErrors.categoria}</p>
						{/if}
					</div>

					<!-- Monthly Budget -->
					<div>
						<label for="presupuesto_mensual" class="block text-sm font-medium text-gray-700 mb-1">
							Presupuesto Mensual (CLP) *
						</label>
						<input
							type="number"
							id="presupuesto_mensual"
							bind:value={formData.presupuesto_mensual}
							min="0"
							step="1000"
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
							placeholder="0"
							class:border-red-300={formErrors.presupuesto_mensual}
						/>
						{#if formErrors.presupuesto_mensual}
							<p class="mt-1 text-sm text-red-600">{formErrors.presupuesto_mensual}</p>
						{/if}
					</div>

					<!-- Form Actions -->
					<div class="flex space-x-3 pt-4">
						<button 
							type="submit" 
							class="btn btn-primary" 
							disabled={$loading}
						>
							{#if $loading}
								⏳ Guardando...
							{:else if editingBudget}
								💾 Actualizar Presupuesto
							{:else}
								💾 Crear Presupuesto
							{/if}
						</button>
						<button 
							type="button" 
							class="btn btn-secondary" 
							on:click={cancelForm}
							disabled={$loading}
						>
							❌ Cancelar
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}

	<!-- Budget Status -->
	<div class="card">
		<div class="card-header">
			<h3 class="text-lg font-medium text-gray-900">Estado de Presupuestos</h3>
		</div>
		<div class="card-body">
			{#if $loading && $budgetStatus.length === 0}
				<div class="text-center py-8">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
					<p class="mt-2 text-gray-500">Cargando presupuestos...</p>
				</div>
			{:else if $budgetStatus.length > 0}
				<div class="space-y-4">
					{#each $budgetStatus as budget (budget.categoria)}
						<div class="border border-gray-200 rounded-lg p-4">
							<div class="flex items-center justify-between mb-3">
								<div class="flex items-center space-x-2">
									<span class="text-lg">{getStatusIcon(budget.estado)}</span>
									<h4 class="font-medium text-gray-900 capitalize">
										{budget.categoria.replace('_', ' ')}
									</h4>
								</div>
								<div class="flex items-center space-x-2">
									<span class={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(budget.estado)}`}>
										{budget.estado.toUpperCase()}
									</span>
									<button 
										type="button"
										class="text-blue-600 hover:text-blue-800 text-sm px-2 py-1 rounded border border-blue-300 hover:bg-blue-50"
										on:click={() => startEdit(budget)}
										title="Editar presupuesto"
									>
										✏️ Editar
									</button>
									<button 
										type="button"
										class="text-red-600 hover:text-red-800 text-sm px-2 py-1 rounded border border-red-300 hover:bg-red-50"
										on:click={() => deleteBudget(budget.categoria)}
										title="Eliminar presupuesto"
									>
										🗑️ Eliminar
									</button>
								</div>
							</div>
							
							<!-- Progress Bar -->
							<div class="mb-3">
								<div class="flex justify-between text-sm text-gray-600 mb-1">
									<span>Gastado: {formatCurrency(budget.gastado_actual)}</span>
									<span>Presupuesto: {formatCurrency(budget.presupuesto_mensual)}</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-2">
									<div 
										class={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(budget.porcentaje_usado)}`}
										style="width: {Math.min(budget.porcentaje_usado, 100)}%"
									></div>
								</div>
								<div class="text-right text-xs text-gray-500 mt-1">
									{budget.porcentaje_usado.toFixed(1)}% usado
								</div>
							</div>
							
							<!-- Remaining Budget -->
							<div class="text-sm text-gray-600">
								{#if budget.presupuesto_mensual - budget.gastado_actual >= 0}
									<span class="text-green-600">
										Disponible: {formatCurrency(budget.presupuesto_mensual - budget.gastado_actual)}
									</span>
								{:else}
									<span class="text-red-600">
										Sobrepasado por: {formatCurrency(budget.gastado_actual - budget.presupuesto_mensual)}
									</span>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="text-center py-8 text-gray-500">
					<div class="text-4xl mb-2">🎯</div>
					<p>No hay presupuestos configurados</p>
					<p class="text-sm mt-1">Crea tu primer presupuesto para comenzar a monitorear tus gastos</p>
				</div>
			{/if}
		</div>
	</div>
</div>
