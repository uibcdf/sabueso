import {build} from 'esbuild';
import fs from 'node:fs';
const outdir='../../sabueso/explorer/_assets';
await build({entryPoints:['src/app.tsx'],outdir,bundle:true,format:'esm',target:'es2022',
  minify:true,legalComments:'inline',define:{'process.env.NODE_ENV':'"production"'}});
fs.copyFileSync('index.html',`${outdir}/index.html`);
const notices=[];
for(const [name,file] of [['react','LICENSE'],['react-dom','LICENSE'],['scheduler','LICENSE'],['dockview-react','LICENCE.md'],['dockview','LICENCE.md'],['dockview-core','LICENCE.md']]){
  const pkg=JSON.parse(fs.readFileSync(`node_modules/${name}/package.json`,'utf8'));
  notices.push(`${name} ${pkg.version}\n${fs.readFileSync(`node_modules/${name}/${file}`,'utf8')}`);
}
fs.writeFileSync(`${outdir}/notices.txt`,notices.join('\n\n--------\n\n'));
