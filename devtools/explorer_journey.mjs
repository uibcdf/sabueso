// Actual product receiving through Qt's renderer and native QWidget capture.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {connectNative} from './standalone_probe/cdp_driver.mjs';
const args=process.argv.slice(2), option=name=>{const index=args.indexOf(name);return index<0?undefined:args[index+1];};
const output=path.resolve(option('--output')),card=path.resolve(option('--card'));
fs.mkdirSync(output,{recursive:false});
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const before=hash(card), children=[],logs=[];
const result={format:'sabueso.explorer_journey@1',scope:'Actual first Qt Card product slice; owned Linux Xvfb software request; no molecular/native-platform qualification',checks:{},errors:[]};
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
  let application=launch(option('--python')||'python',['-m','sabueso.explorer',...(args.includes('--empty')?[]:['--card',card]),'--output-directory',path.join(output,'readings'),'--debug-port',String(port),'--capture-directory',output],'application',env);
  await until(async()=>{try{browser=await connectNative(`http://127.0.0.1:${port}`);return true;}catch{return false;}},'actual Qt application');
  let page=browser.contexts()[0].pages()[0];page.on('pageerror',error=>result.errors.push(String(error)));
  if(args.includes('--empty')){await page.waitForFunction(()=>!!document.querySelector('.welcome button:not(:disabled)'));result.checks.empty_entry_visible=true;const {root}=await page.send('DOM.getDocument');const {nodeId}=await page.send('DOM.querySelector',{nodeId:root.nodeId,selector:'input[type=file]'});await page.send('DOM.setFileInputFiles',{nodeId,files:[card]});}
  await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'),null,{timeout:60000});
  const current=()=>page.evaluate(()=>({ref:document.querySelector('[data-view-ref]').dataset.viewRef,result:document.querySelector('[data-view-ref]').dataset.resultRef,text:document.querySelector('[data-testid="reading-text"]').textContent}));
  const original=await current();
  if(args.includes('--receive-presentation')){
    const state=()=>page.evaluate(async()=>await(await fetch('/api/panel')).json());
    const start=await state();result.checks.native_profile_overview=start.panel.orientation!==null&&await page.evaluate(()=>document.querySelectorAll('.overview-field').length>=5);
    const initialRevision=start.panel.revision;
    await page.getByRole('button',{name:'Inspect original field'}).first().click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,original.ref);
    result.checks.original_overview_field_opens=!!(await state()).panel.trail?.length;
    await page.getByRole('button',{name:'Card overview'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original.ref);result.checks.exact_trail_return=true;
    if(start.panel.profile==='protein'){
      await page.locator('[data-topic="sequence"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,original.ref);
      let next=(await state()).panel.items.find(i=>i.label==='Primary sequence');await page.locator('[data-item-ref="'+next.ref+'"] .item-actions button').first().click();const field=(await state()).panel;
      next=field.items.find(i=>i.label==='value');await page.locator('[data-item-ref="'+next.ref+'"] .item-actions button').first().click();await page.waitForFunction(()=>!!document.querySelector('[data-testid="sequence-strip"]'));
      const text=(await state()).panel.full_text.text;result.checks.sequence_preserves_exact_text=await page.evaluate(expected=>[...document.querySelectorAll('.sequence-line code')].map(x=>x.textContent.replaceAll(' ','')).join('')===expected,text);
      result.checks.sequence_positions_scope_explicit=await page.evaluate(()=>document.querySelector('[aria-label="Complete retained text"]').textContent.includes('not mapped structure or isoform coordinates'));
      const beforeAnnotations=await current();await page.locator('[data-topic="annotated_regions"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,beforeAnnotations.ref);
      await page.getByRole('button',{name:'Table'}).click();await page.waitForFunction(()=>!!document.querySelector('.table-items .value-cell'));
      result.checks.native_annotation_cells_visible=true;
    }else if(start.panel.profile==='disease'){
      await page.locator('[data-topic="classification"]').click();await page.waitForFunction(()=>!![...document.querySelectorAll('button')].find(b=>b.textContent==='Relationship graph'));
      const before=await state();await page.getByRole('button',{name:'Relationship graph'}).click();await page.waitForFunction(()=>!!document.querySelector('.graph-edge'));
      result.checks.source_graph_preserves_native_reading=(await state()).panel.revision===before.panel.revision;
      result.checks.source_graph_has_exact_page_edges=await page.evaluate(count=>document.querySelectorAll('.graph-edge').length===count,before.panel.graph.edges.length);
      await page.locator('.graph-edge button').first().click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.panel.view_ref);
      await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,before.panel.view_ref);result.checks.graph_record_back_exact=true;
    }else if(start.panel.profile==='small_molecule'){
      const prior=await current();await page.locator('[data-topic="properties"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,prior.ref);
      await page.getByRole('button',{name:'Table'}).click();await page.waitForFunction(()=>!!document.querySelector('.table-items .value-cell'));result.checks.native_property_cells_visible=true;
      result.checks.property_unit_retained=await page.evaluate(()=>document.querySelector('.table-items').textContent.includes('dalton'));
    }
    const beforeSources=await current();await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,beforeSources.ref);const sources=await current();await page.getByRole('button',{name:'Open'}).first().click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sources.ref);
    result.checks.original_source_remains_accessible=(await current()).text.includes('asserted_value');
    await page.getByRole('button',{name:'Overview'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original.ref);
    result.checks.native_return_overview_retained=(await state()).panel.revision!==initialRevision;
    result.opened_text_excerpt=(await current()).text.slice(0,100);
    result.scope='Actual Qt nature-specific original overview, native cell values/units, sequence or source graph, source and exact history; Linux/Xvfb only';
  }else{
  await page.locator('[data-topic="content"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,original.ref);
  const content=await current();
  result.checks.topic_navigation=content.ref!==original.ref;
  await page.getByRole('button',{name:'Open'}).first().click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,content.ref);
  const opened=await current();
  await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,content.ref);
  result.checks.exact_back=true;
  const beforeSource=await current();await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,beforeSource.ref);
  const sources=await current();await page.getByRole('button',{name:'Open'}).first().click();
  await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sources.ref);
  result.checks.original_source_opened=(await current()).text.includes('asserted_value');
  await page.getByRole('button',{name:'Save reading'}).click();await page.waitForFunction(()=>document.querySelector('[role="status"]').textContent.includes('Reading saved'),null,{timeout:120000});
  const saved=await current();await page.getByRole('button',{name:'Reopen saved'}).click();
  await page.waitForFunction(()=>document.querySelector('[data-view-ref] .eyebrow').textContent==='Original saved reading');
  const reopened=await current();result.checks.original_saved_reading_reopened=reopened.result===saved.result && reopened.text.includes('Saved exploration');
  await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,saved.ref);
  result.checks.saved_return_preserved=true;
  await page.getByRole('button',{name:'Float reading'}).click();await delay(200);
  result.checks.reading_survives_floating=(await current()).ref===saved.ref;
  await page.getByRole('button',{name:'Reset layout'}).click();await delay(200);
  result.checks.reading_survives_reset=(await current()).ref===saved.ref;
  if(args.includes('--receive-uploaded-reading')){
    const directory=path.join(output,'readings'),name=fs.readdirSync(directory).find(n=>n.endsWith('.json.gz'));if(!name)throw new Error('No original saved file to receive');
    await page.getByRole('button',{name:'Open reading…',exact:true}).click();const {root}=await page.send('DOM.getDocument');const {nodeId}=await page.send('DOM.querySelector',{nodeId:root.nodeId,selector:'input[type=file]'});await page.send('DOM.setFileInputFiles',{nodeId,files:[path.join(directory,name)]});
    await page.waitForFunction(()=>document.querySelector('[role="status"]').textContent.includes('Original reading opened'));
    const received=await current();result.checks.external_original_file_opened=received.result===saved.result&&received.text.includes('Saved exploration');
    result.checks.original_does_not_require_session_save_state=await page.evaluate(()=>[...document.querySelectorAll('.actions button')].find(b=>b.textContent==='Reopen saved').disabled);
  }
  if(args.includes('--receive-layout')){
    const layoutReading=await current();
    await page.getByRole('button',{name:'Float reading'}).click();
    await page.getByRole('button',{name:'Save layout'}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Presentation layout saved'));
    const stored=await page.evaluate(async()=>await(await fetch('/api/panel')).json());
    result.checks.presentation_saved_separately=stored.presentation.layout.format==='sabueso.presentation_layout@1'&&!JSON.stringify(stored.presentation.layout).includes('asserted_value');
    await page.send('Page.reload');await until(async()=>{try{return await page.evaluate(()=>!!document.querySelector('[data-view-ref]')&&document.querySelector('[role=status]')?.textContent.includes('Presentation layout restored'));}catch(error){if(String(error).includes('Cannot find context with specified id'))return false;throw error;}},'new renderer context and restored presentation');
    result.checks.layout_reload_preserves_exact_reading=(await current()).ref===layoutReading.ref;
    const restored=await page.evaluate(async()=>await(await fetch('/api/panel')).json());
    result.checks.saved_presentation_unchanged=JSON.stringify(restored.presentation.layout)===JSON.stringify(stored.presentation.layout);
    result.checks.floating_position_restored=await page.evaluate(()=>!!document.querySelector('.dv-groupview-floating'));
    await page.getByRole('button',{name:'Reset layout'}).click();await delay(200);
    result.checks.reset_uses_default_instead_of_saved_float=await page.evaluate(()=>!document.querySelector('.dv-groupview-floating'));
    await page.locator('[aria-label="Close Knowledge"]').click();await until(()=>page.evaluate(()=>!document.querySelector('[data-view-ref]')),'closed Knowledge panel');
    await page.getByRole('button',{name:'Float reading'}).click();await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'));
    result.checks.reopen_closed_knowledge_preserves_reading=(await current()).ref===layoutReading.ref;
    await page.getByRole('button',{name:'Reset layout'}).click();await delay(200);
  }
  result.opened_text_excerpt=opened.text.slice(0,100);
  }
  if(args.includes('--receive-recovery')){
    const retained=await current();await page.getByRole('button',{name:'Save workspace',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Workspace saved:'),null,{timeout:120000});
    const saved=await page.evaluate(async()=>await(await fetch('/api/panel')).json()),file=path.join(output,'readings',saved.workspace_saved_file);result.recovery_workspace_sha256=hash(file);
    // Only this launcher's direct, positively identified service child is stopped.
    // Never search or terminate Python processes belonging to another session.
    const childPath=`/proc/${application.pid}/task/${application.pid}/children`;
    const owned=fs.readFileSync(childPath,'utf8').trim().split(/\s+/).filter(Boolean).map(Number).filter(pid=>{
      try{const cmd=fs.readFileSync(`/proc/${pid}/cmdline`,'utf8').split('\0');return cmd[1]==='-m'&&cmd[2]==='sabueso.explorer._service'&&fs.readFileSync(`/proc/${pid}/status`,'utf8').includes(`PPid:\t${application.pid}\n`);}catch{return false;}
    });
    if(owned.length!==1)throw new Error('The receiver cannot identify exactly its own service child');
    process.kill(owned[0],'SIGTERM');await until(()=>!fs.existsSync(`/proc/${owned[0]}`),'owned service exit');
    result.checks.qt_window_survives_service_failure=application.exitCode===null&&application.signalCode===null;
    await page.getByRole('button',{name:'Overview',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('The reading service is unavailable'));
    result.checks.service_failure_explained_and_reading_retained=(await current()).ref===retained.ref;
    await browser.close();browser=undefined;application.kill('SIGTERM');await until(()=>application.exitCode!==null||application.signalCode!==null,'owned old window exit');
    application=launch(option('--python')||'python',['-m','sabueso.explorer','--reading',file,'--output-directory',path.join(output,'restarted-readings'),'--debug-port',String(port),'--capture-directory',output],'restarted-application',env);
    await until(async()=>{try{browser=await connectNative(`http://127.0.0.1:${port}`);return true;}catch{return false;}},'explicit restarted Qt application');
    page=browser.contexts()[0].pages()[0];page.on('pageerror',error=>result.errors.push(String(error)));await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'),null,{timeout:60000});
    const restored=await page.evaluate(async()=>await(await fetch('/api/panel')).json());result.checks.explicit_restart_restores_original_workspace=restored.panel.mode==='saved'&&restored.panel.view_ref===retained.ref&&restored.panel.result_ref===retained.result;
    result.checks.restart_preserves_saved_file=hash(file)===result.recovery_workspace_sha256;
    const previous=restored.panel.trail.at(-1);if(!previous)throw new Error('No retained trail to receive after restart');await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,retained.ref);result.checks.original_back_available_after_restart=true;
    result.scope+='; controlled owned service loss and explicit saved-workspace application restart, without automatic unsaved recovery';
  }
  await page.screenshot({path:path.join(output,'renderer.png')});
  fs.writeFileSync(path.join(output,'capture-request'),'capture');await until(()=>fs.existsSync(path.join(output,'native.png')) && fs.statSync(path.join(output,'native.png')).size>1000,'native composition capture');
  result.checks.actual_native_capture=fs.statSync(path.join(output,'native.png')).size>1000;
  result.checks.input_unchanged=hash(card)===before;
  result.checks.no_script_errors=result.errors.length===0;
  result.input_sha256=before;
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
