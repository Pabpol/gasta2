<script>
  import { onMount } from 'svelte';
  
  let budgets = [];
  let loading = true;
  let error = null;
  
  onMount(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/presupuestos');
      if (response.ok) {
        budgets = await response.json();
      } else {
        error = 'Failed to load budgets';
      }
    } catch (err) {
      error = err.message;
      console.error('Error:', err);
    } finally {
      loading = false;
    }
  });
</script>

<h1>Test API Page</h1>

{#if loading}
  <p>Loading...</p>
{:else if error}
  <p>Error: {error}</p>
{:else}
  <p>Found {budgets.length} budgets:</p>
  <ul>
    {#each budgets as budget}
      <li>{budget.categoria}: ${budget.presupuesto_mensual}</li>
    {/each}
  </ul>
{/if}
