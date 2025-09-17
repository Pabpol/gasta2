<script lang="ts">
	import { onMount } from 'svelte';
	import { incomeActions, income, loading, error } from '$lib/stores/data';
	import { formatCurrency, formatDate } from '$lib/utils/api';
	
	// Form state
	let formData = {
		descripcion: '',
		monto_clp: 0,
		fecha: new Date().toISOString().split('T')[0], // Today's date
		contraparte: ''
	};
	
	let showForm = false;
	let formErrors: Record<string, string> = {};
	
	// Load income data on mount
	onMount(() => {
		incomeActions.loadAll();
	});
	
	async function handleSubmit(event: Event) {
		event.preventDefault();
		
		// Reset errors
		formErrors = {};
		
		// Validation
		if (!formData.descripcion.trim()) {
			formErrors.descripcion = 'La descripción es requerida';
		}
		if (formData.monto_clp <= 0) {
			formErrors.monto_clp = 'El monto debe ser mayor a 0';
		}
		if (!formData.fecha) {
			formErrors.fecha = 'La fecha es requerida';
		}
		
		// If there are errors, don't submit
		if (Object.keys(formErrors).length > 0) {
			return;
		}
		
		try {
			await incomeActions.create({
				descripcion: formData.descripcion.trim(),
				monto_clp: formData.monto_clp,
				fecha: formData.fecha,
				contraparte: formData.contraparte.trim() || undefined
			});
			
			// Reset form on success
			formData = {
				descripcion: '',
				monto_clp: 0,
				fecha: new Date().toISOString().split('T')[0],
				contraparte: ''
			};
			showForm = false;
		} catch (err) {
			// Error is handled by the store
			console.error('Error creating income:', err);
		}
	}
	
	function cancelForm() {
		formData = {
			descripcion: '',
			monto_clp: 0,
			fecha: new Date().toISOString().split('T')[0],
			contraparte: ''
		};
		formErrors = {};
		showForm = false;
	}
</script>

<svelte:head>
	<title>Ingresos - Gasta2</title>
</svelte:head>

<div class="px-4 py-6 sm:px-0">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Gestión de Ingresos</h1>
		<p class="mt-2 text-gray-600">Registra y visualiza tus ingresos</p>
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

	<!-- Add Income Button -->
	{#if !showForm}
		<div class="mb-6">
			<button 
				class="btn btn-primary" 
				onclick={() => showForm = true}
			>
				➕ Agregar Ingreso
			</button>
		</div>
	{/if}

	<!-- Add Income Form -->
	{#if showForm}
		<div class="mb-8 card">
			<div class="card-header">
				<h3 class="text-lg font-medium text-gray-900">Nuevo Ingreso</h3>
			</div>
			<div class="card-body">
				<form onsubmit={handleSubmit} class="space-y-4">
					<!-- Description -->
					<div>
						<label for="descripcion" class="block text-sm font-medium text-gray-700 mb-1">
							Descripción *
						</label>
						<input
							type="text"
							id="descripcion"
							bind:value={formData.descripcion}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
							placeholder="Ej: Sueldo, Freelance, Venta..."
							class:border-red-300={formErrors.descripcion}
						/>
						{#if formErrors.descripcion}
							<p class="mt-1 text-sm text-red-600">{formErrors.descripcion}</p>
						{/if}
					</div>

					<!-- Amount -->
					<div>
						<label for="monto_clp" class="block text-sm font-medium text-gray-700 mb-1">
							Monto (CLP) *
						</label>
						<input
							type="number"
							id="monto_clp"
							bind:value={formData.monto_clp}
							min="0"
							step="1"
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
							placeholder="0"
							class:border-red-300={formErrors.monto_clp}
						/>
						{#if formErrors.monto_clp}
							<p class="mt-1 text-sm text-red-600">{formErrors.monto_clp}</p>
						{/if}
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
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
							class:border-red-300={formErrors.fecha}
						/>
						{#if formErrors.fecha}
							<p class="mt-1 text-sm text-red-600">{formErrors.fecha}</p>
						{/if}
					</div>

					<!-- Counterpart (optional) -->
					<div>
						<label for="contraparte" class="block text-sm font-medium text-gray-700 mb-1">
							Contraparte (opcional)
						</label>
						<input
							type="text"
							id="contraparte"
							bind:value={formData.contraparte}
							class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
							placeholder="Ej: Empresa, Cliente..."
						/>
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
							{:else}
								💾 Guardar Ingreso
							{/if}
						</button>
						<button 
							type="button" 
							class="btn btn-secondary" 
							onclick={cancelForm}
							disabled={$loading}
						>
							❌ Cancelar
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}

	<!-- Income List -->
	<div class="card">
		<div class="card-header">
			<h3 class="text-lg font-medium text-gray-900">Historial de Ingresos</h3>
		</div>
		<div class="card-body">
			{#if $loading && $income.length === 0}
				<div class="text-center py-8">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
					<p class="mt-2 text-gray-500">Cargando ingresos...</p>
				</div>
			{:else if $income.length > 0}
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
									Monto
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Contraparte
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							{#each $income as incomeItem (incomeItem.id)}
								<tr class="hover:bg-gray-50">
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
										{formatDate(incomeItem.fecha)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
										{incomeItem.descripcion}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
										{formatCurrency(incomeItem.monto_clp)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
										{incomeItem.contraparte || '-'}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<div class="text-center py-8 text-gray-500">
					<div class="text-4xl mb-2">💰</div>
					<p>No hay ingresos registrados</p>
					<p class="text-sm mt-1">Agrega tu primer ingreso usando el botón de arriba</p>
				</div>
			{/if}
		</div>
	</div>
</div>
