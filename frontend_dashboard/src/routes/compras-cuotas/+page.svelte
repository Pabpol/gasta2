<script lang="ts">
	import { onMount } from 'svelte';
	import { installmentPurchasesApi, type InstallmentPurchase, type CreateInstallmentPurchaseRequest, type UpcomingInstallmentPayment, type InstallmentPurchaseSummary } from '$lib/utils/api';
	import { formatCurrency, formatDate } from '$lib/utils/api';

	// State management
	let installmentPurchases: InstallmentPurchase[] = [];
	let upcomingPayments: UpcomingInstallmentPayment[] = [];
	let summary: InstallmentPurchaseSummary | null = null;
	let loading = true;
	let error: string | null = null;

	// Form states
	let showCreateForm = false;
	let showPaymentForm = false;
	let selectedPurchase: InstallmentPurchase | null = null;
	let formLoading = false;
	let formError: string | null = null;
	let formSuccess: string | null = null;

	// Create form data
	let createFormData: CreateInstallmentPurchaseRequest = {
		descripcion: '',
		installment_total_amount: 0,
		installment_total_installments: 12,
		categoria: 'deudas',
		medio: 'TC',
		installment_interest_rate: 0,
		installment_first_payment_date: new Date().toISOString().split('T')[0],
		installment_payment_frequency: 'monthly'
	};

	// Payment form data
	let paymentFormData = {
		payment_amount: 0,
		payment_date: new Date().toISOString().split('T')[0]
	};

	// Available options
	const categories = [
		{ value: 'deudas', label: '💳 Deudas' },
		{ value: 'educacion', label: '📚 Educación' },
		{ value: 'hogar', label: '🏠 Hogar' },
		{ value: 'transporte', label: '🚗 Transporte' },
		{ value: 'salud', label: '🏥 Salud' },
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
		{ value: 'monthly', label: '📊 Mensual' },
		{ value: 'weekly', label: '📆 Semanal' }
	];

	// Load data on mount
	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		try {
			loading = true;
			error = null;

			// Load all data in parallel
			const [purchases, upcoming, summaryData] = await Promise.all([
				installmentPurchasesApi.getAll(),
				installmentPurchasesApi.getUpcoming(30),
				installmentPurchasesApi.getSummary()
			]);

			installmentPurchases = purchases;
			upcomingPayments = upcoming;
			summary = summaryData;

		} catch (err) {
			error = err instanceof Error ? err.message : 'Error al cargar datos de compras en cuotas';
		} finally {
			loading = false;
		}
	}

	async function handleCreate(event: Event) {
		event.preventDefault();

		if (!createFormData.descripcion.trim()) {
			formError = 'La descripción es requerida';
			return;
		}

		if (createFormData.installment_total_amount <= 0) {
			formError = 'El monto total debe ser mayor a 0';
			return;
		}

		if (createFormData.installment_total_installments <= 0) {
			formError = 'El número de cuotas debe ser mayor a 0';
			return;
		}

		formLoading = true;
		formError = null;
		formSuccess = null;

		try {
			await installmentPurchasesApi.create(createFormData);

			formSuccess = 'Compra en cuotas creada exitosamente';

			// Reset form
			createFormData = {
				descripcion: '',
				installment_total_amount: 0,
				installment_total_installments: 12,
				categoria: 'deudas',
				medio: 'TC',
				installment_interest_rate: 0,
				installment_first_payment_date: new Date().toISOString().split('T')[0],
				installment_payment_frequency: 'monthly'
			};

			// Reload data
			await loadData();

			// Hide form after success
			showCreateForm = false;

		} catch (err) {
			formError = err instanceof Error ? err.message : 'Error al crear compra en cuotas';
		} finally {
			formLoading = false;
		}
	}

	async function handlePayment(event: Event) {
		event.preventDefault();

		if (!selectedPurchase) return;

		if (paymentFormData.payment_amount <= 0) {
			formError = 'El monto del pago debe ser mayor a 0';
			return;
		}

		formLoading = true;
		formError = null;
		formSuccess = null;

		try {
			await installmentPurchasesApi.recordPayment({
				purchase_id: selectedPurchase.id,
				payment_amount: paymentFormData.payment_amount,
				payment_date: paymentFormData.payment_date
			});

			formSuccess = `Pago de ${formatCurrency(paymentFormData.payment_amount)} registrado exitosamente`;

			// Reset form
			paymentFormData = {
				payment_amount: 0,
				payment_date: new Date().toISOString().split('T')[0]
			};

			// Reload data
			await loadData();

			// Hide form after success
			showPaymentForm = false;
			selectedPurchase = null;

		} catch (err) {
			formError = err instanceof Error ? err.message : 'Error al registrar pago';
		} finally {
			formLoading = false;
		}
	}

	function openPaymentForm(purchase: InstallmentPurchase) {
		selectedPurchase = purchase;
		paymentFormData.payment_amount = purchase.installment_installment_amount;
		showPaymentForm = true;
	}

	async function handleDelete(id: string, descripcion: string) {
		if (!confirm(`¿Estás seguro de que quieres eliminar "${descripcion}"?\n\nEsta acción no se puede deshacer.`)) {
			return;
		}

		try {
			await installmentPurchasesApi.delete(id);
			await loadData();
		} catch (err) {
			alert(`Error al eliminar: ${err instanceof Error ? err.message : 'Error desconocido'}`);
		}
	}

	function getProgressPercentage(purchase: InstallmentPurchase): number {
		if (purchase.installment_total_installments === 0) return 0;
		return (purchase.installment_paid_installments / purchase.installment_total_installments) * 100;
	}

	function getProgressColor(purchase: InstallmentPurchase): string {
		const percentage = getProgressPercentage(purchase);
		if (percentage < 25) return 'bg-red-500';
		if (percentage < 50) return 'bg-yellow-500';
		if (percentage < 75) return 'bg-blue-500';
		return 'bg-green-500';
	}

	function getDaysUntilDueColor(days: number): string {
		if (days < 0) return 'text-red-600 font-bold'; // Overdue
		if (days <= 3) return 'text-orange-600 font-semibold'; // Due soon
		if (days <= 7) return 'text-yellow-600'; // This week
		return 'text-gray-600'; // Future
	}

	function calculateInstallmentAmount(): number {
		const total = createFormData.installment_total_amount;
		const installments = createFormData.installment_total_installments;
		const interest = createFormData.installment_interest_rate || 0;

		if (interest > 0) {
			const totalWithInterest = total * (1 + (interest / 100));
			return totalWithInterest / installments;
		}

		return total / installments;
	}
</script>

<svelte:head>
	<title>Compras en Cuotas - Gasta2</title>
</svelte:head>

<div class="px-4 py-6 sm:px-0">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Compras en Cuotas</h1>
		<p class="mt-2 text-gray-600">Gestiona tus compras grandes divididas en pagos mensuales</p>
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

	<!-- Success/Error Messages -->
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
					<h3 class="text-sm font-medium text-red-800">Error</h3>
					<div class="mt-2 text-sm text-red-700">{formError}</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Summary Cards -->
	{#if summary}
		<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
			<div class="card">
				<div class="card-body">
					<div class="flex items-center">
						<div class="text-2xl">💰</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-gray-600">Deuda Total</p>
							<p class="text-2xl font-bold text-red-600">{formatCurrency(summary.total_debt)}</p>
						</div>
					</div>
				</div>
			</div>

			<div class="card">
				<div class="card-body">
					<div class="flex items-center">
						<div class="text-2xl">📊</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-gray-600">Compras Activas</p>
							<p class="text-2xl font-bold text-blue-600">{summary.active_purchases}</p>
						</div>
					</div>
				</div>
			</div>

			<div class="card">
				<div class="card-body">
					<div class="flex items-center">
						<div class="text-2xl">📅</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-gray-600">Próximos Pagos</p>
							<p class="text-2xl font-bold text-orange-600">{summary.upcoming_payments.length}</p>
						</div>
					</div>
				</div>
			</div>

			<div class="card">
				<div class="card-body">
					<div class="flex items-center">
						<div class="text-2xl">💳</div>
						<div class="ml-4">
							<p class="text-sm font-medium text-gray-600">Compromiso Mensual</p>
							<p class="text-2xl font-bold text-purple-600">{formatCurrency(summary.monthly_commitment)}</p>
						</div>
					</div>
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
				➕ Nueva Compra en Cuotas
			{/if}
		</button>
		<button
			class="btn btn-secondary"
			on:click={loadData}
			disabled={loading}
		>
			🔄 Actualizar
		</button>
	</div>

	<!-- Create Form -->
	{#if showCreateForm}
		<div class="mb-8 bg-white shadow rounded-lg p-6">
			<div class="flex justify-between items-center mb-6">
				<h2 class="text-lg font-semibold text-gray-900">Nueva Compra en Cuotas</h2>
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
						bind:value={createFormData.descripcion}
						placeholder="Ej: Diplomado en Arquitectura de Software, Laptop Dell, etc."
						class="input-field"
						required
						disabled={formLoading}
					/>
				</div>

				<!-- Amount and Installments -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="total_amount" class="block text-sm font-medium text-gray-700 mb-1">
							Monto Total (CLP) *
						</label>
						<input
							type="number"
							id="total_amount"
							bind:value={createFormData.installment_total_amount}
							placeholder="650000"
							min="1"
							class="input-field"
							required
							disabled={formLoading}
						/>
					</div>

					<div>
						<label for="installments" class="block text-sm font-medium text-gray-700 mb-1">
							Número de Cuotas *
						</label>
						<input
							type="number"
							id="installments"
							bind:value={createFormData.installment_total_installments}
							min="1"
							max="360"
							class="input-field"
							required
							disabled={formLoading}
						/>
					</div>
				</div>

				<!-- Interest Rate -->
				<div>
					<label for="interest_rate" class="block text-sm font-medium text-gray-700 mb-1">
						Tasa de Interés (%)
					</label>
					<input
						type="number"
						id="interest_rate"
						bind:value={createFormData.installment_interest_rate}
						placeholder="0"
						min="0"
						max="100"
						step="0.1"
						class="input-field"
						disabled={formLoading}
					/>
					<p class="mt-1 text-xs text-gray-500">
						Cuota calculada: <strong>{formatCurrency(calculateInstallmentAmount())}</strong>
					</p>
				</div>

				<!-- Category and Payment Method -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="categoria" class="block text-sm font-medium text-gray-700 mb-1">
							Categoría *
						</label>
						<select
							id="categoria"
							bind:value={createFormData.categoria}
							class="input-field"
							required
							disabled={formLoading}
						>
							{#each categories as category}
								<option value={category.value}>{category.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<label for="medio" class="block text-sm font-medium text-gray-700 mb-1">
							Medio de Pago *
						</label>
						<select
							id="medio"
							bind:value={createFormData.medio}
							class="input-field"
							required
							disabled={formLoading}
						>
							{#each paymentMethods as method}
								<option value={method.value}>{method.label}</option>
							{/each}
						</select>
					</div>
				</div>

				<!-- First Payment Date and Frequency -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="first_payment" class="block text-sm font-medium text-gray-700 mb-1">
							Primera Cuota *
						</label>
						<input
							type="date"
							id="first_payment"
							bind:value={createFormData.installment_first_payment_date}
							class="input-field"
							required
							disabled={formLoading}
						/>
					</div>

					<div>
						<label for="frequency" class="block text-sm font-medium text-gray-700 mb-1">
							Frecuencia de Pago *
						</label>
						<select
							id="frequency"
							bind:value={createFormData.installment_payment_frequency}
							class="input-field"
							required
							disabled={formLoading}
						>
							{#each frequencies as freq}
								<option value={freq.value}>{freq.label}</option>
							{/each}
						</select>
					</div>
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
							💾 Crear Compra en Cuotas
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

	<!-- Payment Form Modal -->
	{#if showPaymentForm && selectedPurchase}
		<div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
			<div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
				<div class="mt-3">
					<h3 class="text-lg font-medium text-gray-900 mb-4">
						Registrar Pago - {selectedPurchase.descripcion}
					</h3>

					<form on:submit|preventDefault={handlePayment} class="space-y-4">
						<div>
							<label for="payment_amount" class="block text-sm font-medium text-gray-700 mb-1">
								Monto del Pago (CLP) *
							</label>
							<input
								type="number"
								id="payment_amount"
								bind:value={paymentFormData.payment_amount}
								min="1"
								class="input-field"
								required
								disabled={formLoading}
							/>
							<p class="mt-1 text-xs text-gray-500">
								Cuota sugerida: {formatCurrency(selectedPurchase.installment_installment_amount)}
							</p>
						</div>

						<div>
							<label for="payment_date" class="block text-sm font-medium text-gray-700 mb-1">
								Fecha del Pago *
							</label>
							<input
								type="date"
								id="payment_date"
								bind:value={paymentFormData.payment_date}
								class="input-field"
								required
								disabled={formLoading}
							/>
						</div>

						<div class="flex space-x-3">
							<button
								type="submit"
								class="btn btn-primary"
								disabled={formLoading}
							>
								{#if formLoading}
									⏳ Registrando...
								{:else}
									💰 Registrar Pago
								{/if}
							</button>
							<button
								type="button"
								class="btn btn-secondary"
								on:click={() => { showPaymentForm = false; selectedPurchase = null; }}
								disabled={formLoading}
							>
								❌ Cancelar
							</button>
						</div>
					</form>
				</div>
			</div>
		</div>
	{/if}

	<!-- Upcoming Payments -->
	{#if upcomingPayments.length > 0}
		<div class="mb-8">
			<h3 class="text-lg font-semibold text-gray-900 mb-4">📅 Próximos Pagos</h3>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each upcomingPayments as payment (payment.purchase_id)}
					<div class="card">
						<div class="card-body">
							<div class="flex justify-between items-start mb-2">
								<h4 class="font-medium text-gray-900 truncate">{payment.descripcion}</h4>
								<span class={`text-sm font-medium ${getDaysUntilDueColor(payment.days_until_due)}`}>
									{payment.days_until_due <= 0 ? 'VENCIDO' : `${payment.days_until_due} días`}
								</span>
							</div>
							<div class="space-y-1 text-sm text-gray-600">
								<p>Cuota {payment.installment_number} de {payment.total_installments}</p>
								<p class="font-semibold text-lg text-red-600">{formatCurrency(payment.installment_amount)}</p>
								<p>Vence: {formatDate(payment.next_payment_date)}</p>
								<p>Restante: {formatCurrency(payment.remaining_balance)}</p>
							</div>
							<button
								class="btn btn-primary w-full mt-3"
								on:click={() => openPaymentForm(installmentPurchases.find(p => p.id === payment.purchase_id)!)}
							>
								💰 Registrar Pago
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Installment Purchases List -->
	<div class="card">
		<div class="card-header">
			<h3 class="text-lg font-medium text-gray-900">Compras en Cuotas</h3>
		</div>
		<div class="card-body">
			{#if loading}
				<div class="text-center py-8">
					<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
					<p class="mt-2 text-gray-500">Cargando compras en cuotas...</p>
				</div>
			{:else if installmentPurchases.length > 0}
				<div class="space-y-6">
					{#each installmentPurchases as purchase (purchase.id)}
						<div class="border border-gray-200 rounded-lg p-6">
							<div class="flex justify-between items-start mb-4">
								<div class="flex-1">
									<h4 class="text-lg font-semibold text-gray-900">{purchase.descripcion}</h4>
									<p class="text-sm text-gray-600 mt-1">
										{purchase.installment_paid_installments} de {purchase.installment_total_installments} cuotas pagadas
									</p>
								</div>
								<div class="flex space-x-2">
									<button
										class="btn btn-primary"
										on:click={() => openPaymentForm(purchase)}
									>
										💰 Registrar Pago
									</button>
									<button
										class="text-red-600 hover:text-red-900 transition-colors duration-200"
										on:click={() => handleDelete(purchase.id, purchase.descripcion)}
										title="Eliminar compra en cuotas"
									>
										🗑️
									</button>
								</div>
							</div>

							<!-- Progress Bar -->
							<div class="mb-4">
								<div class="flex justify-between text-sm text-gray-600 mb-1">
									<span>Progreso</span>
									<span>{Math.round(getProgressPercentage(purchase))}%</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-2">
									<div
										class={`h-2 rounded-full ${getProgressColor(purchase)}`}
										style="width: {getProgressPercentage(purchase)}%"
									></div>
								</div>
							</div>

							<!-- Details Grid -->
							<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
								<div>
									<p class="text-gray-600">Monto Total</p>
									<p class="font-semibold text-red-600">{formatCurrency(purchase.installment_total_amount)}</p>
								</div>
								<div>
									<p class="text-gray-600">Cuota</p>
									<p class="font-semibold">{formatCurrency(purchase.installment_installment_amount)}</p>
								</div>
								<div>
									<p class="text-gray-600">Saldo Restante</p>
									<p class="font-semibold text-red-600">{formatCurrency(purchase.installment_remaining_balance)}</p>
								</div>
								<div>
									<p class="text-gray-600">Próxima Cuota</p>
									<p class="font-semibold">{formatDate(purchase.installment_first_payment_date)}</p>
								</div>
							</div>

							{#if purchase.installment_interest_rate > 0}
								<div class="mt-3 text-sm text-gray-600">
									<span class="font-medium">Interés:</span> {purchase.installment_interest_rate}%
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{:else}
				<div class="text-center py-8 text-gray-500">
					<div class="text-4xl mb-2">💳</div>
					<p>No tienes compras en cuotas registradas</p>
					<p class="text-sm mt-1">Registra tu primera compra grande dividida en cuotas</p>
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
		@apply px-4 py-2 rounded-md font-medium transition-colors duration-200 text-sm;
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