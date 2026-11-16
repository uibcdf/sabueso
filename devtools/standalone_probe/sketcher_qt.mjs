// Experimental provider receiving, not a product adapter or scientific oracle.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import net from 'node:net';
import {createServer} from 'node:http';
import {setTimeout as delay} from 'node:timers/promises';
import {fileURLToPath} from 'node:url';
import {connectNative} from './cdp_driver.mjs';
import {launchOwned} from './owned_process.mjs';

const args=process.argv.slice(2),option=name=>{const index=args.indexOf(name);if(index<0||!args[index+1])throw new Error('Missing '+name);return args[index+1];};
const output=path.resolve(option('--output')),packed=path.resolve(option('--package')),corpus=path.resolve(option('--corpus'));
fs.mkdirSync(output,{recursive:false});
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const corpusBytes=fs.readFileSync(corpus),manifest=JSON.parse(fs.readFileSync(path.join(packed,'package.json'),'utf8'));
if(manifest.name!=='@uibcdf/molsyssketcher'||manifest.exports['.'].import!=='./dist/index.js')throw new Error('Receive the actual package public ESM entry');
if(corpusBytes.length>8*1024**2)throw new Error('Use a bounded prepared corpus');
const modules=new Map();
for(const name of fs.readdirSync(path.join(packed,'dist'))){if(/^[a-z-]+\.js$/.test(name))modules.set('/sketcher/'+name,fs.readFileSync(path.join(packed,'dist',name)));}
if(!modules.has('/sketcher/index.js'))throw new Error('No public entry in packed resources');
const root=path.dirname(fileURLToPath(import.meta.url)),requests=[],owned=[];
const receipt={format:'sabueso.sketcher_qt_receiving@1',scope:'Packed experimental molecular SVG surface in actual Sabueso Qt host; frozen RDKit corpus, Linux/Xvfb; no product/source-Card/interaction/3D or public-package qualification',checks:{},errors:[],corpus_sha256:hash(corpusBytes),module_sha256:Object.fromEntries([...modules].map(([name,raw])=>[name,hash(raw)])),package:{name:manifest.name,version:manifest.version,private:manifest.private}};
let browser,service;
function check(name,value){receipt.checks[name]=value===true;if(!value)throw new Error('Failed receiving: '+name);}
async function until(work,label){const end=Date.now()+30000;while(Date.now()<end){for(const child of owned)child.assertRunning(label);if(await work())return;await delay(100);}throw new Error('Timed out: '+label);}
function launch(command,parameters,name,env){const result=launchOwned(command,parameters,{name,logPath:path.join(output,name+'.log'),env});owned.push(result);return result.child;}
try{
  const hostHtml=fs.readFileSync(path.join(root,'sketcher_host.html')),hostJs=fs.readFileSync(path.join(root,'sketcher_host.mjs'));
  service=createServer((request,response)=>{
    const pathname=new URL(request.url,'http://127.0.0.1').pathname;requests.push(pathname);
    const raw=pathname==='/'?hostHtml:pathname==='/host.js'?hostJs:pathname==='/corpus.json'?corpusBytes:modules.get(pathname);
    response.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; object-src 'none'");
    response.setHeader('X-Content-Type-Options','nosniff');response.setHeader('Cache-Control','no-store');
    response.setHeader('Content-Type',pathname==='/'?'text/html':pathname.endsWith('.json')?'application/json':'application/javascript');
    response.writeHead(raw?200:404);response.end(raw??'Not found');
  });
  await new Promise((resolve,reject)=>{service.once('error',reject);service.listen(0,'127.0.0.1',resolve);});
  const url='http://127.0.0.1:'+service.address().port;
  const env={...process.env,LIBGL_ALWAYS_SOFTWARE:'1',LIBGL_DRIVERS_PATH:'/usr/lib/x86_64-linux-gnu/dri',QT_QPA_PLATFORM:'xcb',QTWEBENGINE_CHROMIUM_FLAGS:'--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --disable-gpu-compositing --num-raster-threads=1'};
  const xvfb=launch('Xvfb',['-displayfd','3','-screen','0','1280x900x24','-nolisten','tcp'],'xvfb',env);let display='';xvfb.stdio[3].on('data',chunk=>{display+=chunk.toString();});
  await until(()=>/^\d+\n/.test(display),'owned display');env.DISPLAY=':'+display.trim();
  const reserve=net.createServer();await new Promise(resolve=>reserve.listen(0,'127.0.0.1',resolve));const port=reserve.address().port;await new Promise(resolve=>reserve.close(resolve));
  const python=args.includes('--python')?option('--python'):'python';
  launch(python,['-c','import sys; from pathlib import Path; from sabueso.explorer._qt import _window; _window(sys.argv[1], debug_port=int(sys.argv[2]), capture_directory=Path(sys.argv[3]))',url,String(port),output],'qt',env);
  await until(async()=>{try{browser=await connectNative('http://127.0.0.1:'+port);return true;}catch{return false;}},'native Qt debug endpoint');
  const page=browser.contexts()[0].pages()[0];page.on('pageerror',error=>receipt.errors.push(String(error)));
  const network=[];page.on('request',request=>network.push(request.url()));
  await page.waitForFunction(()=>!!window.sketcherReceiving);
  receipt.browser=await page.send('Browser.getVersion');
  check('two_independent_real_svg_views',await page.evaluate(()=>document.querySelectorAll('[data-molsyssketcher-view]').length===2));
  receipt.cases=await page.evaluate(async()=>{
    const {a,b,corpus}=sketcherReceiving,rows=[];
    for(const entry of corpus){
      const result=await a.replace(entry.document);if(result.status!=='accepted')throw new Error('Provider corpus refused: '+entry.id);
      const {scene,document:accepted}=a.state.accepted,svg=document.querySelector('#a svg');let discrepancy=0;
      const labels=[...svg.querySelectorAll('[data-layer="chemical-labels"] text')];
      for(const width of [260,540]){a.resize(width,320);for(let i=0;i<labels.length;i++){const box=labels[i].getBBox(),expected=scene.glyphs[i].box;for(const key of ['x','y','width','height'])discrepancy=Math.max(discrepancy,Math.abs(box[key]-expected[key]));}}
      const eventTarget=scene.atoms[0];a.setSelection({kind:'atom',semanticId:eventTarget.semanticId},scene.generation);
      const selection=a.state.selection;
      rows.push({id:entry.id,atoms:scene.atoms.length,bonds:scene.bonds.length,declared_counts_match:scene.atoms.length===entry.document.atoms.length&&scene.bonds.length===entry.document.bonds.length,glyph_count:labels.length,max_glyph_error:discrepancy,original_unchanged:JSON.stringify(accepted.original)===JSON.stringify(entry.document.original),context_unchanged:JSON.stringify(accepted.context)===JSON.stringify(entry.document.context),selected_exact_atom:selection.semanticId===eventTarget.semanticId&&selection.instanceId==='sabueso-qt-a'&&selection.documentId===entry.document.id&&selection.sceneGeneration===scene.generation,independent_other_document:b.state.accepted.document.id===corpus[0].document.id&&b.state.selection===null});
    }
    return rows;
  });
  check('twelve_prepared_controls_received',receipt.cases.length===12);
  check('declared_atom_and_bond_counts_retained',receipt.cases.every(row=>row.declared_counts_match));
  check('measured_labels_match_native_svg_boxes',receipt.cases.every(row=>row.max_glyph_error<.05));
  check('original_context_and_exact_selection_retained',receipt.cases.every(row=>row.original_unchanged&&row.context_unchanged&&row.selected_exact_atom));
  check('independent_view_survives_all_replacements',receipt.cases.every(row=>row.independent_other_document));
  await page.evaluate(async()=>{const h=sketcherReceiving;await h.a.replace(h.corpus[0].document);h.events.length=0;document.querySelector('#a svg').focus();});
  async function key(name,code,number){await page.send('Input.dispatchKeyEvent',{type:'keyDown',key:name,code,windowsVirtualKeyCode:number,nativeVirtualKeyCode:number});await page.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,code,windowsVirtualKeyCode:number});}
  await key('ArrowRight','ArrowRight',39);await page.keyboard.press('Enter');
  check('real_keyboard_selects_declared_atom',await page.evaluate(()=>sketcherReceiving.events.at(-1)?.kind==='atom'&&sketcherReceiving.events.at(-1).semanticId===sketcherReceiving.a.state.accepted.scene.atoms[0].semanticId));
  const point=await page.evaluate(()=>{const {a}=sketcherReceiving;a.setSelection(null,a.state.accepted.scene.generation);const atom=a.state.accepted.scene.atoms[1],svg=document.querySelector('#a svg'),p=new DOMPoint(atom.position.x,atom.position.y).matrixTransform(svg.getScreenCTM());return {x:p.x,y:p.y,semanticId:atom.semanticId};});
  for(const type of ['mouseMoved','mousePressed','mouseReleased'])await page.send('Input.dispatchMouseEvent',{type,x:point.x,y:point.y,...(type==='mouseMoved'?{}:{button:'left',clickCount:1})});
  check('real_pointer_selects_exact_atom',await page.evaluate(expected=>sketcherReceiving.a.state.selection?.semanticId===expected,point.semanticId));
  check('real_hover_carries_exact_context',await page.evaluate(expected=>sketcherReceiving.hovers.some(p=>p?.semanticId===expected&&p?.documentId===sketcherReceiving.a.state.accepted.document.id),point.semanticId));
  const beforeWheel=await page.evaluate(()=>JSON.stringify(sketcherReceiving.a.state.viewport));
  await page.send('Input.dispatchMouseEvent',{type:'mouseWheel',x:point.x,y:point.y,deltaX:0,deltaY:-120});await delay(100);
  check('real_wheel_changes_viewport',await page.evaluate(before=>JSON.stringify(sketcherReceiving.a.state.viewport)!==before,beforeWheel));
  const beforeDrag=await page.evaluate(()=>({camera:JSON.stringify(sketcherReceiving.a.state.viewport),selection:JSON.stringify(sketcherReceiving.a.state.selection),events:sketcherReceiving.events.length}));
  await page.send('Input.dispatchMouseEvent',{type:'mousePressed',x:point.x,y:point.y,button:'left',buttons:1,clickCount:1});
  await page.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:point.x+24,y:point.y+12,button:'left',buttons:1});
  await page.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:point.x+24,y:point.y+12,button:'left',buttons:0,clickCount:1});
  check('real_drag_pans_without_selecting',await page.evaluate(before=>JSON.stringify(sketcherReceiving.a.state.viewport)!==before.camera&&JSON.stringify(sketcherReceiving.a.state.selection)===before.selection&&sketcherReceiving.events.length===before.events,beforeDrag));
  const lifecycle=await page.evaluate(async()=>{
    const {a,b,corpus}=sketcherReceiving,initial=JSON.stringify(a.state.accepted.document),g=a.state.accepted.scene.generation;
    const before=JSON.stringify(a.state.viewport);a.zoomBy(1.8);const zoomed=JSON.stringify(a.state.viewport);a.panBy(18,-12);const panned=JSON.stringify(a.state.viewport);a.fit();
    const invalid=structuredClone(corpus[0].document);invalid.depiction.atoms[0].atomId='absent';const refused=await a.replace(invalid);
    const preserved=JSON.stringify(a.state.accepted.document)===initial&&a.state.accepted.scene.generation===g;
    await a.replace(corpus[1].document);let stale=false;try{a.setSelection({kind:'atom',semanticId:corpus[0].document.atoms[0].id},g);}catch(error){stale=error.code==='invalid-input';}
    const accepted=a.state.accepted,container=document.querySelector('#a'),temporary=document.createElement('section');document.body.append(temporary);temporary.append(container);a.resize(420,320);document.querySelector('.views').prepend(container);a.resize(540,370);temporary.remove();
    const retained=a.state.accepted===accepted;
    const exportText=a.exportSvg(),parsed=new DOMParser().parseFromString(exportText,'image/svg+xml'),meta=JSON.parse(parsed.querySelector('metadata').textContent);
    window.__retiredSvg=document.querySelector('#a svg');const eventCount=sketcherReceiving.events.length;a.dispose();
    const afterDispose=await a.replace(corpus[0].document);window.__retiredSvg.dispatchEvent(new MouseEvent('click',{bubbles:true}));delete window.__retiredSvg;
    return {zoom_changed:before!==zoomed,pan_changed:zoomed!==panned,source_unchanged_during_navigation:preserved,failed_replacement_preserves_accepted:refused.status==='failed'&&preserved,stale_generation_refused:stale,reparent_and_resize_retains_document:retained,export_retains_source_and_nonphysical_scope:JSON.stringify(meta.source)===JSON.stringify(corpus[1].document.original.source)&&meta.coordinates==='nonphysical-drawing'&&!parsed.querySelector('[data-layer="selection"]')?.children.length,owned_disposal_removes_only_one_view:!document.querySelector('#a svg')&&!!document.querySelector('#b svg')&&b.state.lifecycle==='ready',disposed_replace_is_refused:afterDispose.status==='disposed',retired_svg_emits_no_selection:sketcherReceiving.events.length===eventCount};
  });
  for(const [name,value] of Object.entries(lifecycle))check(name,value);
  await page.evaluate(async()=>{const h=sketcherReceiving;h.a=h.api.createMolecularSvgView(document.querySelector('#a'),{instanceId:'sabueso-qt-remounted'});await h.a.replace(h.corpus.find(item=>item.id==='tetra-a').document);h.describe();});
  check('fresh_remount_draws_without_restarting_qt',await page.evaluate(()=>document.querySelectorAll('[data-molsyssketcher-view]').length===2));
  check('each_drawing_exposes_its_own_original',await page.evaluate(()=>{const text=document.querySelector('#source').textContent;return ['a','b'].every(name=>text.includes(name.toUpperCase()+': '+sketcherReceiving[name].state.accepted.document.id+' · original '+JSON.stringify(sketcherReceiving[name].state.accepted.document.original.source)));}));
  await page.screenshot({path:path.join(output,'renderer.png')});fs.writeFileSync(path.join(output,'capture-request'),'capture');await until(()=>fs.existsSync(path.join(output,'native.png')),'native QWidget capture');
  await page.evaluate(()=>{sketcherReceiving.a.dispose();sketcherReceiving.b.dispose();});
  check('all_views_release_their_svg',await page.evaluate(()=>document.querySelectorAll('[data-molsyssketcher-view]').length===0));
  check('prepared_input_file_unchanged',hash(fs.readFileSync(corpus))===receipt.corpus_sha256);
  check('no_browser_script_errors',receipt.errors.length===0);
  check('observed_requests_stay_on_owned_origin',network.every(address=>address.startsWith(url+'/')));
  receipt.observed_request_paths=[...new Set(requests)];receipt.state='passed';
}catch(error){receipt.state='failed';receipt.errors.push(String(error));process.exitCode=1;}
finally{
  if(browser)await browser.close();
  for(const item of [...owned].reverse()){const child=item.child;if(child.exitCode===null&&child.signalCode===null){child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),delay(5000)]);if(child.exitCode===null&&child.signalCode===null)child.kill('SIGKILL');}}
  receipt.owned_logs=owned.map(item=>item.closeLog());
  if(service)await new Promise(resolve=>service.close(resolve));
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({state:receipt.state,checks:Object.keys(receipt.checks).length,errors:receipt.errors}));
}
