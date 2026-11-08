<script lang="ts">
  import '../app.css';
  let { children } = $props();
</script>

<div class="min-h-screen bg-slate-50 text-slate-900 selection:bg-slate-900 selection:text-white">
  {@render children()}
</div>
