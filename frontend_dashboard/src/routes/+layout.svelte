<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { initializeStores } from '$lib/stores/data';

	let { children } = $props();
	let mobileMenuOpen = $state(false);

	onMount(() => {
		// Initialize data stores when app starts
		initializeStores();
	});

	// Navigation items
	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '📊' },
		{ href: '/ingresos', label: 'Ingresos', icon: '💰' },
		{ href: '/presupuestos', label: 'Presupuestos', icon: '🎯' },
		{ href: '/gastos', label: 'Gastos', icon: '📝' },
		{ href: '/gastos-recurrentes', label: 'Gastos Recurrentes', icon: '🔄' },
		{ href: '/configuracion', label: 'Configuración', icon: '⚙️' }
	];

	function isActiveRoute(href: string, currentPath: string): boolean {
		if (href === '/') {
			return currentPath === '/';
		}
		return currentPath.startsWith(href);
	}

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}
</script>

<svelte:head>
	<title>Gasta2 - Dashboard de Gastos</title>
	<meta name="description" content="Sistema de gestión de gastos personales" />
</svelte:head>

<div class="min-h-full bg-gray-50">
	<!-- Navigation -->
	<nav class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex justify-between h-16">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<a href="/" class="text-xl font-bold text-gray-900">💰 Gasta2</a>
					</div>
					<div class="hidden md:ml-6 md:flex md:space-x-8">
						{#each navItems as item}
							<a 
								href={item.href} 
								class={`px-3 py-2 text-sm font-medium ${
									isActiveRoute(item.href, $page.url.pathname)
										? 'text-primary-600 border-b-2 border-primary-600'
										: 'text-gray-500 hover:text-gray-700'
								}`}
							>
								<span class="mr-1">{item.icon}</span>
								{item.label}
							</a>
						{/each}
					</div>
				</div>
				<div class="flex items-center">
					<div class="text-sm text-gray-500 mr-4">
						{new Date().toLocaleDateString('es-CL', { 
							year: 'numeric', 
							month: 'long', 
							day: 'numeric' 
						})}
					</div>
					<!-- Mobile menu button -->
					<div class="md:hidden">
						<button
							type="button"
							class="bg-white inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
							onclick={toggleMobileMenu}
						>
							<span class="sr-only">Open main menu</span>
							{#if mobileMenuOpen}
								<svg class="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							{:else}
								<svg class="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
								</svg>
							{/if}
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Mobile menu -->
		{#if mobileMenuOpen}
			<div class="md:hidden">
				<div class="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t border-gray-200">
					{#each navItems as item}
						<a
							href={item.href}
							class={`block px-3 py-2 text-base font-medium ${
								isActiveRoute(item.href, $page.url.pathname)
									? 'text-primary-600 bg-primary-50'
									: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
							}`}
							onclick={() => mobileMenuOpen = false}
						>
							<span class="mr-2">{item.icon}</span>
							{item.label}
						</a>
					{/each}
				</div>
			</div>
		{/if}
	</nav>

	<!-- Main content -->
	<main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
		{@render children?.()}
	</main>
</div>
