<script lang="ts">
	import { onMount } from 'svelte';
	import { dashboardApi } from '$lib/utils/api';

	let periodConfig = {
		pay_day: 25,
		period_name: '',
		days_until_pay: 0,
		next_pay_date: ''
	};

	let newPayDay = 25;
	let loading = true;
	let saving = false;
	let error: string | null = null;
	let success: string | null = null;

	async function loadConfig() {
		loading = true;
		error = null;
		
		try {
			const response = await dashboardApi.getPeriodConfig();
			
			// Extract data directly (no nested .data)
			periodConfig = response;
			newPayDay = periodConfig.pay_day;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error loading configuration';
			console.error('Config load error:', err);
		} finally {
			loading = false;
		}
	}

	async function saveConfig() {
		if (newPayDay < 1 || newPayDay > 31) {
			error = 'El día de pago debe estar entre 1 y 31';
			return;
		}

		saving = true;
		error = null;
		success = null;
		
		try {
			const response = await dashboardApi.updatePeriodConfig({
				pay_day: newPayDay
			});
			
			// Extract data directly (no nested .data)
			periodConfig = response;
			success = 'Configuración actualizada correctamente';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Error saving configuration';
			console.error('Config save error:', err);
		} finally {
			saving = false;
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('es-CL', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	onMount(() => {
		loadConfig();
	});
</script>

<svelte:head>
	<title>Configuración - Gasta2</title>
</svelte:head>

<div class="px-4 py-6 sm:px-0">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Configuración</h1>
		<p class="mt-2 text-gray-600">Configura tu día de pago y período financiero</p>
	</div>

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
		</div>
	{:else}
		<div class="max-w-2xl">
			<!-- Current Period Info -->
			<div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
				<h2 class="text-lg font-semibold text-blue-900 mb-4">Período Actual</h2>
				<div class="space-y-2 text-blue-800">
					<p><strong>Período:</strong> {periodConfig?.period_name || 'Cargando...'}</p>
					<p><strong>Día de pago:</strong> {periodConfig?.pay_day || 25} de cada mes</p>
					{#if periodConfig?.next_pay_date}
						<p><strong>Próximo pago:</strong> {formatDate(periodConfig.next_pay_date)}</p>
					{/if}
					<p><strong>Días restantes:</strong> {periodConfig?.days_until_pay || 0} días</p>
				</div>
			</div>

			<!-- Configuration Form -->
			<div class="bg-white shadow rounded-lg p-6">
				<h2 class="text-lg font-semibold text-gray-900 mb-6">Cambiar Configuración</h2>
				
				<form on:submit|preventDefault={saveConfig}>
					<div class="mb-6">
						<label for="pay_day" class="block text-sm font-medium text-gray-700 mb-2">
							Día de Pago
						</label>
						<input
							type="number"
							id="pay_day"
							bind:value={newPayDay}
							min="1"
							max="31"
							class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
							placeholder="25"
						/>
						<p class="mt-2 text-sm text-gray-500">
							Día del mes en que recibes tu sueldo (1-31)
						</p>
					</div>

					{#if error}
						<div class="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
							<div class="flex">
								<div class="flex-shrink-0">
									<span class="text-red-400">❌</span>
								</div>
								<div class="ml-3">
									<p class="text-sm text-red-800">{error}</p>
								</div>
							</div>
						</div>
					{/if}

					{#if success}
						<div class="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
							<div class="flex">
								<div class="flex-shrink-0">
									<span class="text-green-400">✅</span>
								</div>
								<div class="ml-3">
									<p class="text-sm text-green-800">{success}</p>
								</div>
							</div>
						</div>
					{/if}

					<div class="flex justify-end">
						<button
							type="submit"
							disabled={saving || newPayDay === periodConfig.pay_day}
							class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{#if saving}
								<span class="mr-2">⏳</span>
								Guardando...
							{:else}
								Guardar Cambios
							{/if}
						</button>
					</div>
				</form>
			</div>

			<!-- Help Section -->
			<div class="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
				<h3 class="text-md font-semibold text-gray-900 mb-3">¿Cómo funciona?</h3>
				<div class="space-y-2 text-sm text-gray-700">
					<p><strong>Período financiero:</strong> Se calcula desde el día de pago hasta el día anterior del siguiente mes.</p>
					<p><strong>Ejemplo:</strong> Si tu día de pago es el 25, tu período será del 25 de un mes al 24 del siguiente.</p>
					<p><strong>Dashboard:</strong> Todas las estadísticas se calcularán basadas en este período, no en meses naturales.</p>
					<p><strong>Balance:</strong> Incluirá ingresos y gastos del período completo, reflejando tu situación financiera real.</p>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	input[type="number"] {
		appearance: textfield;
	}
	input[type="number"]::-webkit-outer-spin-button,
	input[type="number"]::-webkit-inner-spin-button {
		appearance: none;
		margin: 0;
	}
</style>
