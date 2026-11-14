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
  const fixtureService=launch(python,['devtools/explorer_fixture_service.py','--bootstrap',bootstrap,'--output-directory',path.join(output,'readings'),'--fixture-directory',fixtures,...(args.includes('--receive-candidates')?['--synthetic-candidates']:[])],'fixture-service',env);
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
  if(args.includes('--receive-candidates')){
    const original=await query('smiles','CCO','ambiguous');result.checks.ambiguity_preserves_previous_reading=original.panel.view_ref===error.panel.view_ref;
    result.checks.explicit_source_candidates_visible=original.resolution.choices.length===2&&await page.evaluate(()=>document.querySelector('[aria-label="Source query result"]').textContent.includes('does not merge candidates'));
    result.checks.original_candidate_context_visible=await page.evaluate(()=>document.querySelector('[aria-label="Explicit source follow-up queries"]').textContent.includes('Synthetic ambiguity receiving control'));
    await page.getByRole('button',{name:'Query pubchem:3717450',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[aria-label="Source query result"] strong')?.textContent==='resolved');
    const selected=await state();result.checks.candidate_opens_separate_record_query=selected.resolution.kind==='pubchem'&&selected.resolution.query==='pubchem:3717450'&&!JSON.parse(selected.resolution.original_text).resolution.decision.structure;
    await page.getByRole('button',{name:'Save workspace',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Workspace saved:'),null,{timeout:120000});
    await page.getByRole('button',{name:'Reopen workspace',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Original workspace reopened'),null,{timeout:120000});result.checks.candidate_report_reopens_original=(await state()).resolution.kind==='pubchem'&&(await state()).resolution.mode==='saved';
    const callsBeforeReturn=fs.readFileSync(path.join(output,'readings','source-calls.jsonl'),'utf8');await page.getByRole('button',{name:'Return to previous query',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[aria-label="Source query result"] strong')?.textContent==='ambiguous');
    const previous=await state(),choicePairs=choices=>choices.map(c=>[c.ref,c.entity_ref]);result.checks.exact_original_ambiguity_and_candidates_return=previous.resolution.original_text===original.resolution.original_text&&JSON.stringify(choicePairs(previous.resolution.choices))===JSON.stringify(choicePairs(original.resolution.choices))&&fs.readFileSync(path.join(output,'readings','source-calls.jsonl'),'utf8')===callsBeforeReturn;
  }
  if(args.includes('--receive-workspace')){
    const beforeWorkspace=await state(),beforeCalls=fs.readFileSync(path.join(output,'readings','source-calls.jsonl'),'utf8');
    await page.getByRole('button',{name:'Save workspace'}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Workspace saved:'));
    const saved=await state(),file=path.join(output,'readings',saved.workspace_saved_file);result.workspace_file=file;
    await page.getByRole('button',{name:'Reopen workspace'}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Original workspace reopened'));
    const reopened=await state();result.checks.workspace_exact_reading=reopened.panel.view_ref===beforeWorkspace.panel.view_ref&&reopened.panel.mode==='saved';
    result.checks.workspace_original_query_report=reopened.resolution.original_text===beforeWorkspace.resolution.original_text&&reopened.resolution.mode==='saved';
    result.checks.workspace_source_history_retained=reopened.can_return_query===true;
    await page.getByRole('button',{name:'Open reading…'}).click();const {root}=await page.send('DOM.getDocument');const {nodeId}=await page.send('DOM.querySelector',{nodeId:root.nodeId,selector:'input[type=file]'});await page.send('DOM.setFileInputFiles',{nodeId,files:[file]});await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Original reading opened'));
    result.checks.workspace_independent_upload=(await state()).panel.view_ref===beforeWorkspace.panel.view_ref;
    result.checks.workspace_reopening_does_not_query_sources=fs.readFileSync(path.join(output,'readings','source-calls.jsonl'),'utf8')===beforeCalls;
  }
  if(args.includes('--receive-cancellation')){
    const readings=path.join(output,'readings'),pause=path.join(readings,'pause-next-query'),waiting=path.join(readings,'query-waiting'),release=path.join(readings,'release-query');
    async function delayed(){await input('uniprot','P52270');await page.waitForFunction(()=>!document.querySelector('#entry-query').disabled&&![...document.querySelectorAll('button')].find(b=>b.textContent==='Query public sources').disabled);fs.writeFileSync(pause,'pause');await page.getByRole('button',{name:'Query public sources'}).click();await until(()=>fs.existsSync(waiting),'synthetic source wait');await page.waitForFunction(()=>document.querySelector('[aria-label="Source query progress"] strong')?.textContent==='Querying public sources'&&!document.querySelector('header button').disabled);}
    const beforeDelay=await state();await delayed();
    result.checks.submitted_form_leaves_reading_space=await page.evaluate(()=>!document.querySelector('.query-drawer')&&document.querySelector('.application').getBoundingClientRect().height>=360);
    const initial=(await state()).panel.view_ref;await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,initial);const browsing=await state();
    result.checks.reading_remains_available_during_query=browsing.query_job.state==='running'&&fs.existsSync(waiting);
    await page.getByRole('button',{name:'Cancel query'}).click();await page.waitForFunction(()=>document.querySelector('[aria-label="Source query progress"]').textContent.includes('Result discarded'));
    fs.writeFileSync(release,'release');await page.waitForFunction(async()=>!(await(await fetch('/api/query')).json()).query_job.worker_running);
    const cancelled=await state();result.checks.cancelled_result_does_not_replace_reading=cancelled.panel.view_ref===browsing.panel.view_ref&&cancelled.resolution.original_text===beforeDelay.resolution.original_text;
    await delayed();const origin=(await state()).panel.view_ref;await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,origin);const previous=await state();fs.writeFileSync(release,'release');
    await page.waitForFunction(()=>!![...document.querySelectorAll('button')].find(b=>b.textContent==='Open result'));
    result.checks.changed_reading_waits_for_explicit_adoption=(await state()).panel.view_ref===previous.panel.view_ref;
    await page.getByRole('button',{name:'Open result'}).click();await page.waitForFunction(async()=>{const s=await(await fetch('/api/panel')).json();return s.panel.profile==='protein'&&s.query_job.state==='opened';});result.checks.explicit_ready_result_opens=true;
    const callsBeforeReturn=fs.readFileSync(path.join(readings,'source-calls.jsonl'),'utf8');await page.getByRole('button',{name:'Return to previous query'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,previous.panel.view_ref);
    result.checks.ready_result_exact_query_return=fs.readFileSync(path.join(readings,'source-calls.jsonl'),'utf8')===callsBeforeReturn;
  }
  await page.screenshot({path:path.join(output,'renderer.png')});fs.writeFileSync(path.join(output,'capture-request'),'capture');
  await until(()=>fs.existsSync(path.join(output,'native.png'))&&fs.statSync(path.join(output,'native.png')).size>1000,'native composition capture');result.checks.actual_native_capture=true;
  const calls=fs.readFileSync(path.join(output,'readings','source-calls.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  result.source_calls=calls;result.checks.only_explicit_source_queries=calls.length===6+(args.includes('--receive-cancellation')?2:0)+(args.includes('--receive-candidates')?2:0);
  if(args.includes('--receive-pending-close')){
    const readings=path.join(output,'readings');fs.writeFileSync(path.join(readings,'pause-next-query'),'pause');await input('uniprot','P52270');await page.waitForFunction(()=>!document.querySelector('#entry-query').disabled);await page.getByRole('button',{name:'Query public sources',exact:true}).click();await until(()=>fs.existsSync(path.join(readings,'query-waiting')),'owned pending source query');
    result.checks.pending_query_is_observed_before_close=(await state()).query_job.worker_running===true;
    const started=performance.now();fixtureService.kill('SIGTERM');await Promise.race([new Promise(resolve=>fixtureService.once('exit',resolve)),delay(8000)]);
    result.pending_service_close_elapsed_s=(performance.now()-started)/1000;result.checks.owned_pending_service_closes_within_deadline=fixtureService.exitCode!==null||fixtureService.signalCode!==null;
    result.checks.closed_service_retires_its_bootstrap=!fs.existsSync(bootstrap);
    result.pending_query_disposition='One additional explicit synthetic query was pending at owned service shutdown; no result was adopted. Completed-call audit above excludes this unfinished request. This receives process-owned worker lifetime, not provider HTTP cancellation.';
    if(!result.checks.owned_pending_service_closes_within_deadline)throw new Error('Owned fixture service did not stop within its shutdown deadline');
  }
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
