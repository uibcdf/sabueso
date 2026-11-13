import { build } from 'esbuild';

await build({
  entryPoints: ['src/app.tsx'],
  outdir: 'dist',
  bundle: true,
  format: 'esm',
  target: 'es2022',
  minify: false,
  sourcemap: true,
  define: { 'process.env.NODE_ENV': '"production"' },
});
