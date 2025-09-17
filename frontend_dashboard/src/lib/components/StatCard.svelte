<script lang="ts">
  export let title: string;
  export let value: number;
  export let change: number | null = null;
  export let icon: string = '💰';
  export let type: 'currency' | 'number' | 'percentage' = 'currency';
  export let variant: 'default' | 'success' | 'danger' | 'warning' = 'default';
  
  function formatValue(val: number): string {
    // For transaction count (number type), just return the number
    if (type === 'number') {
      return val.toString();
    }
    
    if (type === 'currency') {
      return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0,
      }).format(val);
    } else if (type === 'percentage') {
      return `${val.toFixed(1)}%`;
    } else {
      return val.toLocaleString('es-CL');
    }
  }
  
  function getChangeClass(change: number): string {
    if (change > 0) return 'positive';
    if (change < 0) return 'negative';
    return '';
  }
  
  function getVariantClass(variant: string): string {
    switch (variant) {
      case 'success':
        return 'border-l-success-500 bg-success-50';
      case 'danger':
        return 'border-l-danger-500 bg-danger-50';
      case 'warning':
        return 'border-l-warning-500 bg-warning-50';
      default:
        return 'border-l-primary-500 bg-white';
    }
  }
</script>

<div class="stat-card border-l-4 {getVariantClass(variant)}">
  <div class="card-body">
    <div class="flex items-center">
      <div class="flex-shrink-0">
        <div class="text-2xl">{icon}</div>
      </div>
      <div class="ml-4 flex-1">
        <div class="stat-label">{title}</div>
        <div class="stat-value {variant === 'danger' ? 'text-danger-700' : variant === 'success' ? 'text-success-700' : ''}">{formatValue(value)}</div>
        {#if change !== null}
          <div class="stat-change {getChangeClass(change)}">
            {#if change > 0}
              ↗ +{formatValue(Math.abs(change))}
            {:else if change < 0}
              ↙ -{formatValue(Math.abs(change))}
            {:else}
              → Sin cambio
            {/if}
            <span class="text-gray-500 text-xs ml-1">vs mes anterior</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
