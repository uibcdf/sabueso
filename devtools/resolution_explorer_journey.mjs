// Actual product receiving through Qt's renderer and native QWidget capture.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {connectNative} from './standalone_probe/cdp_driver.mjs';
const args=process.argv.slice(2), option=name=>{const index=args.indexOf(name);return index<0?undefined:args[index+1];};
const output=path.resolve(option('--output')),fixtures=path.resolve(option('--fixtures'));
fs.mkdirSync(output,{recursive:false});
const children=[],logs=[];
const result={format:'sabueso.explorer_journey@1',scope:'Actual Qt source-entry UI with native resolution against public frozen sources and network forbidden; no live-source/native-platform qualification',checks:{},errors:[]};
async function until(fn,label){const end=Date.now()+60000;while(Date.now()<end){if(await fn())return;await delay(100);}throw new Error(`Timed out: ${label}`);}
function launch(command,parameters,name,env){const log=fs.openSync(path.join(output,`${name}.log`),'wx');logs.push(log);const child=spawn(command,parameters,{env,cwd:args.includes('--application-root')?option('--application-root'):undefined,stdio:['ignore',log,log,'pipe']});children.push(child);return child;}
let browser;
try{
  const env={...process.env,LIBGL_ALWAYS_SOFTWARE:'1',LIBGL_DRIVERS_PATH:'/usr/lib/x86_64-linux-gnu/dri',QT_QPA_PLATFORM:'xcb',QTWEBENGINE_CHROMIUM_FLAGS:'--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --disable-gpu-compositing --num-raster-threads=1'};
  if(args.includes('--application-root'))env.PYTHONPATH=path.resolve(option('--application-root'));
  const xvfb=launch('Xvfb',['-displayfd','3','-screen','0','1280x900x24','-nolisten','tcp'],'xvfb',env);
  let display='';xvfb.stdio[3].on('data',chunk=>{display+=chunk.toString();});
  await until(()=>/^\d+\n/.test(display),'Xvfb');env.DISPLAY=`:${display.trim()}`;
  const server=net.createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port;await new Promise(resolve=>server.close(resolve));
  const python=option('--python')||'python',bootstrap=path.join(output,'bootstrap.json');
  launch(python,['devtools/explorer_fixture_service.py','--bootstrap',bootstrap,'--output-directory',path.join(output,'readings'),'--fixture-directory',fixtures],'fixture-service',env);
  await until(()=>fs.existsSync(bootstrap),'fixture service bootstrap');
  launch(python,['-c',"import json,sys;from pathlib import Path;from sabueso.explorer._qt import _window;_window(json.loads(Path(sys.argv[1]).read_text())['url'],int(sys.argv[2]),Path(sys.argv[3]))",bootstrap,String(port),output],'application',env);
  await until(async()=>{try{browser=await connectNative(`http://127.0.0.1:${port}`);return true;}catch{return false;}},'actual Qt application');
  const page=browser.contexts()[0].pages()[0];page.on('pageerror',error=>result.errors.push(String(error)));
  await page.waitForFunction(()=>!!document.querySelector('.welcome button:not(:disabled)'));
  result.checks.white_entry_and_four_input_kinds=await page.evaluate(()=>document.querySelector('.welcome')!==null&&document.querySelectorAll('#entry-kind option').length===4);
  const state=()=>page.evaluate(async()=>await(await fetch('/api/panel')).json());
  async function input(kind,text){
    if(await page.evaluate(()=>!document.querySelector('#entry-query')))await page.getByRole('button',{name:'New source query'}).click();
    await page.evaluate(value=>{const e=document.querySelector('#entry-kind');Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(e,value);e.dispatchEvent(new Event('change',{bubbles:true}));},kind);
    await page.locator('#entry-query').focus();await page.send('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await page.send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await page.send('Input.insertText',{text});
  }
  async function query(kind,text,expected){await input(kind,text);const before=(await state()).resolution?.revision;
    await page.getByRole('button',{name:'Query public sources',exact:true}).click();
    await page.waitForFunction(async old=>{const s=await(await fetch('/api/panel')).json();return s.resolution&&s.resolution.revision!==old;},before);
    await page.waitForFunction(()=>!document.querySelector('header button')?.disabled);
    const current=await state();if(current.resolution.status!==expected)throw new Error('Unexpected source outcome: '+current.resolution.status);return current;}
  const pdb=await query('pdb','1TCD','resolved');result.checks.pdb_is_a_record_without_an_invented_card=pdb.panel===null&&pdb.resolution.choices.length===1;
  await page.getByRole('button',{name:'Query sabueso:protein:uniprot:P52270',exact:true}).click();
  await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'));
  result.checks.explicit_source_related_protein=(await state()).resolution.kind==='uniprot';
  await page.locator('[data-topic="sources"]').click();await page.waitForFunction(()=>document.querySelector('[data-view-ref] h2').textContent.toLowerCase().includes('source'));
  const sources=await state();await page.getByRole('button',{name:'Open',exact:true}).first().click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="reading-text"]').textContent.includes('asserted_value'));
  await page.getByRole('button',{name:'Back',exact:true}).click();
  await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,sources.panel.view_ref);
  result.checks.original_source_and_exact_back=true;
  await page.getByRole('button',{name:'Return to previous query',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.welcome')!==null);
  result.checks.exact_pdb_return_without_acquisition=(await state()).resolution.query===pdb.resolution.query;
  const disease=await query('disease','MONDO:0014221','resolved');result.checks.disease_card_and_topics=disease.panel.profile==='disease'&&disease.panel.topics.length>0;
  const smiles=JSON.parse(fs.readFileSync(path.join(fixtures,'pubchem','structures.json'))).lookups[0].query;
  const molecule=await query('smiles',smiles,'resolved');result.checks.source_stated_smiles_identity=molecule.panel.profile==='small_molecule'&&molecule.resolution.original_text.includes('pubchem_structure_lookup');
  const absent=JSON.parse(fs.readFileSync(path.join(fixtures,'pubchem','structures.json'))).lookups[3].query;
  const missing=await query('smiles',absent,'not_found');result.checks.not_found_preserves_previous_reading=missing.panel.view_ref===molecule.panel.view_ref;
  const error=await query('uniprot','P00000','error');result.checks.source_failure_is_distinct_and_preserves_reading=error.panel.view_ref===molecule.panel.view_ref;
  await page.screenshot({path:path.join(output,'renderer.png')});fs.writeFileSync(path.join(output,'capture-request'),'capture');
  await until(()=>fs.existsSync(path.join(output,'native.png'))&&fs.statSync(path.join(output,'native.png')).size>1000,'native composition capture');result.checks.actual_native_capture=true;
  const calls=fs.readFileSync(path.join(output,'readings','source-calls.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  result.source_calls=calls;result.checks.only_explicit_source_queries=calls.length===6;
  result.checks.no_script_errors=result.errors.length===0;
  if(!Object.values(result.checks).every(Boolean))throw new Error('A selected product check failed');
  result.state='passed';
}catch(error){result.state='failed';result.errors.push(String(error));if(browser){try{const p=browser.contexts()[0].pages()[0];result.failure=await p.evaluate(async()=>({status:document.querySelector('[role="status"]')?.textContent,buttons:[...document.querySelectorAll('.actions button')].map(x=>({text:x.textContent,disabled:x.disabled})),panel:await(await fetch('/api/panel')).json()}));await p.screenshot({path:path.join(output,'failure.png')});}catch{}}}
finally{
  if(browser)await browser.close();
  for(const child of [...children].reverse()){if(child.exitCode!==null||child.signalCode!==null)continue;child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),delay(10000)]);if(child.exitCode===null&&child.signalCode===null)child.kill('SIGKILL');}
  for(const log of logs)fs.closeSync(log);
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
  if(result.state!=='passed')process.exitCode=1;
}
