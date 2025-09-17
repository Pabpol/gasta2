<script lang="ts">
  import { onMount } from 'svelte';
  import { Chart, registerables } from 'chart.js';
  
  Chart.register(...registerables);
  
  export let title: string = '';
  export let data: any[] = [];
  export let type: 'doughnut' | 'line' | 'bar' = 'doughnut';
  export let height: number = 300;
  
  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;
  
  $: if (chart && data) {
    updateChart();
  }
  
  onMount(() => {
    createChart();
    return () => {
      if (chart) {
        chart.destroy();
      }
    };
  });
  
  function createChart() {
    if (!canvas || !data.length) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const chartData = prepareChartData();
    
    chart = new Chart(ctx, {
      type,
      data: chartData,
      options: getChartOptions()
    });
  }
  
  function updateChart() {
    if (!chart) return;
    
    const chartData = prepareChartData();
    chart.data = chartData;
    chart.update();
  }
  
  function prepareChartData() {
    if (type === 'doughnut') {
      return {
        labels: data.map(item => item.categoria || item.label),
        datasets: [{
          data: data.map(item => item.total || item.value),
          backgroundColor: [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
            '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6366F1'
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      };
    } else if (type === 'line') {
      return {
        labels: data.map(item => item.month || item.label),
        datasets: [
          {
            label: 'Gastos',
            data: data.map(item => Number(item.expenses) || 0),
            borderColor: '#EF4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.3,
            fill: false
          },
          {
            label: 'Balance',
            data: data.map(item => Number(item.balance) || 0),
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.3,
            fill: false
          }
        ]
      };
    } else {
      return {
        labels: data.map(item => item.label),
        datasets: [{
          label: title,
          data: data.map(item => item.value),
          backgroundColor: '#3B82F6',
          borderColor: '#2563EB',
          borderWidth: 1
        }]
      };
    }
  }
  
  function getChartOptions() {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom' as const,
          labels: {
            padding: 20,
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context: any) {
              const value = context.parsed?.y ?? context.parsed ?? 0;
              const label = context.dataset?.label ?? '';
              
              // Convert to number if it's not already
              const numericValue = typeof value === 'number' ? value : parseFloat(value) || 0;
              
              return `${label}: $${numericValue.toLocaleString('es-CL')}`;
            }
          }
        }
      }
    };
    
    if (type === 'doughnut') {
      return {
        ...baseOptions,
        cutout: '60%',
        plugins: {
          ...baseOptions.plugins,
          legend: {
            ...baseOptions.plugins.legend,
            position: 'right' as const
          }
        }
      };
    } else if (type === 'line') {
      return {
        ...baseOptions,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value: any) {
                return '$' + value.toLocaleString('es-CL');
              }
            }
          }
        }
      };
    } else {
      return {
        ...baseOptions,
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value: any) {
                return '$' + value.toLocaleString('es-CL');
              }
            }
          }
        }
      };
    }
  }
</script>

<div class="chart-container">
  {#if title}
    <h3 class="text-lg font-medium text-gray-900 mb-4">{title}</h3>
  {/if}
  
  {#if data.length > 0}
    <div style="height: {height}px; position: relative;">
      <canvas bind:this={canvas}></canvas>
    </div>
  {:else}
    <div class="flex items-center justify-center h-64 text-gray-500">
      <div class="text-center">
        <div class="text-4xl mb-2">📊</div>
        <div>No hay datos para mostrar</div>
      </div>
    </div>
  {/if}
</div>

<style>
  .chart-container {
    background: white;
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  }
</style>
