// Real Qt/product/Viewer receiving; no provider internals or simulated graphics.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {connectNative} from './standalone_probe/cdp_driver.mjs';
const args=process.argv.slice(2),option=name=>{const i=args.indexOf(name);return i<0?undefined:args[i+1];};
const idleSeconds=Number(option('--observe-idle-seconds')??0),layoutCycles=Number(option('--layout-cycles')??3);
if(!Number.isInteger(idleSeconds)||idleSeconds<0||idleSeconds>30||!Number.isInteger(layoutCycles)||layoutCycles<1||layoutCycles>20)throw new Error('Use an integer idle window of 0–30 seconds and 1–20 layout cycles');
const output=path.resolve(option('--output')),card=path.resolve(option('--card')),model=path.resolve(option('--model'));
fs.mkdirSync(output,{recursive:false});
if(option('--presentation-source')){fs.mkdirSync(path.join(output,'readings'));fs.copyFileSync(option('--presentation-source'),path.join(output,'readings','presentation-layout.json'));}
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const hashes={card:hash(card),model:hash(model)},children=[],logs=[];
const result={format:'sabueso.molecular_explorer_journey@1',scope:'Actual experimental Qt/Viewer product panel; Linux/Xvfb software rendering; no mapped Card identity, stable embedding or native platform qualification',checks:{},errors:[],resource_phases:[]};
async function until(fn,label){const end=Date.now()+60000;while(Date.now()<end){if(await fn())return;await delay(100);}throw new Error('Timed out: '+label);}
function launch(command,parameters,name,env){const log=fs.openSync(path.join(output,name+'.log'),'wx');logs.push(log);const child=spawn(command,parameters,{env,cwd:option('--application-root')?path.resolve(option('--application-root')):undefined,stdio:['ignore',log,log,'pipe']});children.push(child);return child;}
let browser,independentBrowser;
try{
  const env={...process.env,LIBGL_ALWAYS_SOFTWARE:'1',LIBGL_DRIVERS_PATH:'/usr/lib/x86_64-linux-gnu/dri',QT_QPA_PLATFORM:'xcb',QTWEBENGINE_CHROMIUM_FLAGS:'--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --disable-gpu-compositing --num-raster-threads=1'};
  if(option('--application-root'))env.PYTHONPATH=path.resolve(option('--application-root'));
  const xvfb=launch('Xvfb',['-displayfd','3','-screen','0','1400x1000x24','-nolisten','tcp'],'xvfb',env);let display='';xvfb.stdio[3].on('data',chunk=>{display+=chunk.toString();});await until(()=>/^\d+\n/.test(display),'Xvfb');env.DISPLAY=':'+display.trim();
  const server=net.createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;await new Promise(resolve=>server.close(resolve));
  const callerInput=args.includes('--receive-lifetime')?path.join(output,'caller-'+path.basename(model)):model;if(callerInput!==model)fs.copyFileSync(model,callerInput);
  launch(option('--python')||'python',['-m','sabueso.explorer','--card',card,...(args.includes('--layout-fallback')?[]:['--experimental-model',callerInput]),'--output-directory',path.join(output,'readings'),'--debug-port',String(port),'--capture-directory',output],'application',env);
  await until(async()=>{try{browser=await connectNative('http://127.0.0.1:'+port);return true;}catch{return false;}},'actual product');
  const page=browser.contexts()[0].pages()[0];page.on('pageerror',e=>result.errors.push(String(e)));
  await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'));
  const state=()=>page.evaluate(async()=>await(await fetch('/api/molecular')).json());
  const original=await page.evaluate(()=>document.querySelector('[data-view-ref]').dataset.viewRef);
  if(args.includes('--layout-fallback')){
    result.checks.no_model_is_silently_opened=(await state()).molecular===null;
    result.checks.default_layout_explains_unavailable_context=await page.evaluate(message=>document.querySelector('[role=status]').textContent.includes(message),option('--expected-layout-message'));
  }else if(args.includes('--unavailable')){
    const current=(await state()).molecular;
    result.checks.failed_model_keeps_knowledge=current.status==='unavailable'&&!current.client_url;
    result.checks.failure_is_visible=await page.evaluate(()=>document.querySelector('[role=alert]')?.textContent.includes('Molecular preview unavailable'));
  }else{
    await until(async()=>{const m=(await state()).molecular;return m?.initial_renderer_ready&&m.initial_structure_received;},'provider renderer and structure acknowledgments');
    const frame=page.frames().find(f=>f!==page.mainFrame()&&f.url().includes('/session/client'));if(!frame)throw new Error('No live Viewer frame');
    const canvas=frame.locator('canvas').first();await canvas.waitFor();
    result.graphics=await canvas.evaluate(canvas=>{const gl=canvas.getContext('webgl2')||canvas.getContext('webgl');if(!gl)return {webgl:false};const debug=gl.getExtension('WEBGL_debug_renderer_info');return {webgl:true,width:gl.drawingBufferWidth,height:gl.drawingBufferHeight,renderer:gl.getParameter(debug?debug.UNMASKED_RENDERER_WEBGL:gl.RENDERER),error:gl.getError()};});
    result.checks.real_canvas_and_renderer=result.graphics.webgl&&result.graphics.width>0&&result.graphics.height>0&&result.graphics.error===0;
    if(idleSeconds){const start=Date.now()/1000;await delay(idleSeconds*1000);result.resource_phases.push({name:'idle_before_interaction',start_wall_s:start,end_wall_s:Date.now()/1000,scope:'Original product/provider polling retained; no deliberate interaction or animation; software profile'});}
    const activeStart=Date.now()/1000;
    const box=await canvas.boundingBox(),x=box.x+box.width/2,y=box.y+box.height/2;
    await page.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',buttons:1,clickCount:1});
    for(let i=1;i<=6;i++)await page.send('Input.dispatchMouseEvent',{type:'mouseMoved',x:x+i*8,y:y+i*3,button:'left',buttons:1});
    await page.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:x+48,y:y+18,button:'left',buttons:0,clickCount:1});
    await until(async()=>!!(await state()).molecular.camera_snapshot,'public camera observation');await delay(500);
    const before=(await state()).molecular;
    await page.evaluate(()=>{const f=document.querySelector('[data-testid=molecular-frame]');f.dataset.receivedLifetime='retained';});
    for(let i=0;i<layoutCycles;i++){await page.getByRole('button',{name:'Float model'}).click();await delay(200);if(i===0)result.checks.actual_floating_group_observed=await page.evaluate(()=>!!document.querySelector('.dv-groupview-floating'));await page.getByRole('button',{name:'Reset layout'}).click();await delay(200);}
    result.resource_phases.push({name:'rotation_and_layout_cycles',start_wall_s:activeStart,end_wall_s:Date.now()/1000,scope:'One deliberate camera rotation and repeated float/reset; not repeated provider creation/disposal'});
    if(idleSeconds){const start=Date.now()/1000;await delay(idleSeconds*1000);result.resource_phases.push({name:'idle_after_interaction',start_wall_s:start,end_wall_s:Date.now()/1000,scope:'Same viewport retained after layout cycles; software profile'});}
    const after=(await state()).molecular;
    result.checks.reset_returns_to_main_grid=await page.evaluate(()=>document.querySelectorAll('.dv-groupview-floating').length===0);
    const camera=c=>Object.fromEntries(['position','target','up','mode','fov','radius','radiusMax'].map(k=>[k,c[k]]));
    result.lifecycle={cycles:layoutCycles,registrations_before:before.client_registrations,registrations_after:after.client_registrations,camera_before:before.camera_snapshot,camera_after:after.camera_snapshot};
    result.checks.same_live_viewport=before.client_registrations===after.client_registrations&&await page.evaluate(()=>document.querySelector('[data-testid=molecular-frame]').dataset.receivedLifetime==='retained');
    result.checks.camera_survives_layout=JSON.stringify(camera(before.camera_snapshot))===JSON.stringify(camera(after.camera_snapshot));
    result.checks.selection_survives_layout=JSON.stringify(before.active_selection_indices)===JSON.stringify(after.active_selection_indices);
    result.checks.no_inferred_correspondence=after.correspondence==='not_established'&&after.initial_input_digest==='sha256:'+hashes.model;
    result.checks.reading_survives_layout=await page.evaluate(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original);
  }
  if(args.includes('--receive-layout')){
    const before=(await state()).molecular;await page.getByRole('button',{name:'Save layout'}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Presentation layout saved'));
    const saved=await page.evaluate(async()=>await(await fetch('/api/panel')).json());
    result.checks.molecular_presentation_saved_without_scene=saved.presentation.layout.workspace.panels.molecular.contentComponent==='molecular';
    result.checks.saving_layout_keeps_live_model=(await state()).molecular.client_registrations===before.client_registrations&&await page.evaluate(()=>document.querySelector('[data-testid=molecular-frame]').dataset.receivedLifetime==='retained');
  }
  if(args.includes('--receive-lifetime')){
    const peerPort=await new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});
    launch(option('--python')||'python',['-m','sabueso.explorer','--card',card,'--experimental-model',model,'--output-directory',path.join(output,'independent-readings'),'--debug-port',String(peerPort)],'independent',env);
    await until(async()=>{try{independentBrowser=await connectNative('http://127.0.0.1:'+peerPort);return true;}catch{return false;}},'independently owned Qt window');
    const peer=independentBrowser.contexts()[0].pages()[0];peer.on('pageerror',error=>result.errors.push('Independent: '+String(error)));await peer.waitForFunction(()=>!!document.querySelector('[data-view-ref]'));
    const peerState=()=>peer.evaluate(async()=>await(await fetch('/api/molecular')).json());
    await until(async()=>{const m=(await peerState()).molecular;return m?.initial_renderer_ready&&m.initial_structure_received;},'independent live renderer');
    const peerFrame=peer.frames().filter(f=>f!==peer.mainFrame()&&f.url().includes('/session/client')).at(-1);await peerFrame.locator('canvas').first().waitFor();
    const peerBefore=(await peerState()).molecular,origin=new URL((await state()).molecular.client_url).origin;
    fs.writeFileSync(callerInput,'changed task-owned caller input after capture');
    result.checks.caller_mutation_is_separate=hash(callerInput)!==hashes.model&&hash(model)===hashes.model;
    result.runtime_cycles=[];
    for(let cycle=0;cycle<3;cycle++){
      const before=(await state()).molecular;
      await page.getByRole('button',{name:'Close model',exact:true}).click();await until(async()=>{const m=(await state()).molecular;return m.status==='closed'&&m.can_reopen&&!m.client_url;},'owned runtime closed');
      result.checks.closed_runtime_releases_view=await page.evaluate(()=>!document.querySelector('[data-testid=molecular-frame]'));
      result.checks.closed_origin_is_not_listening=await fetch(origin+'/session/client',{signal:AbortSignal.timeout(2000)}).then(()=>false,()=>true);
      const during=(await peerState()).molecular;
      result.checks.independent_live_view_survives_close=during.client_url===peerBefore.client_url&&during.initial_renderer_ready&&during.client_registrations===peerBefore.client_registrations&&await peerFrame.locator('canvas').first().evaluate(c=>c.width>0&&c.height>0);
      result.checks.closed_view_keeps_reading=await page.evaluate(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original);
      if(cycle===0){
        await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,original);await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original);
        await page.send('Page.reload');await delay(500);await until(async()=>{try{return await page.evaluate(()=>!!document.querySelector('[data-view-ref]'));}catch{return false;}},'closed-runtime reading reload');
        result.checks.reload_does_not_open_model=(await state()).molecular.status==='closed'&&!await page.evaluate(()=>!!document.querySelector('[data-testid=molecular-frame]'));
        result.checks.closed_reading_reload_keeps_exact_context=await page.evaluate(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original);
        const blocker=net.createServer();await new Promise((resolve,reject)=>{blocker.once('error',reject);blocker.listen(Number(new URL(origin).port),'127.0.0.1',resolve);});
        try{await page.getByRole('button',{name:'Reopen initial model',exact:true}).click();await until(async()=>{const m=(await state()).molecular;return m.status==='unavailable'&&m.can_reopen;},'occupied-port failure');result.checks.occupied_origin_is_visible=await page.evaluate(()=>!!document.querySelector('[role=alert]'));result.checks.failed_reopen_preserves_reading=await page.evaluate(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,original);}finally{await new Promise(resolve=>blocker.close(resolve));}
      }
      await page.getByRole('button',{name:'Reopen initial model',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Initial model reopened as a fresh view'));
      await page.getByRole('button',{name:'Show model',exact:true}).click();
      await page.waitForFunction(()=>{const r=document.querySelector('.reading[data-view-ref]').getBoundingClientRect(),c=document.querySelector('.orientation').getBoundingClientRect();return r.width>=400&&Math.abs(c.left-r.left)<5&&c.top>r.top;});result.checks.reopened_layout_keeps_reading_space=true;
      await until(async()=>{const m=(await state()).molecular;return m?.initial_renderer_ready&&m.initial_structure_received;},'new initial-copy runtime');
      const current=(await state()).molecular;
      const freshFrame=page.frames().filter(f=>f!==page.mainFrame()&&f.url().includes('/session/client')).at(-1);await freshFrame.locator('canvas').first().waitFor();
      const oldToken=new URLSearchParams(new URL(before.client_url).hash.slice(1)).get('token');
      const staleAuth=await fetch(origin+'/session/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:oldToken})});
      result.checks.old_runtime_capability_is_refused=staleAuth.status===403;
      result.checks.new_runtime_retains_initial_copy=new URL(current.client_url).origin===origin&&current.initial_input_digest==='sha256:'+hashes.model&&current.correspondence==='not_established';
      result.checks.new_runtime_is_explicit=current.client_url!==before.client_url&&current.lifecycle_revision!==before.lifecycle_revision&&await page.evaluate(()=>document.querySelector('[role=status]').textContent.includes('Camera, selection and scene were not restored'));
      result.checks.new_runtime_actually_draws=await freshFrame.locator('canvas').first().evaluate(c=>{const gl=c.getContext('webgl2')||c.getContext('webgl');return !!gl&&gl.drawingBufferWidth>0&&gl.drawingBufferHeight>0&&gl.getError()===0;});
      result.runtime_cycles.push({cycle:cycle+1,closed_listener_retired:result.checks.closed_origin_is_not_listening,independent_view_retained:result.checks.independent_live_view_survives_close,new_runtime_draws:result.checks.new_runtime_actually_draws,initial_copy_binding:result.checks.new_runtime_retains_initial_copy,stale_capability_refused:result.checks.old_runtime_capability_is_refused});
      if(!Object.values(result.runtime_cycles.at(-1)).every(Boolean)||!Object.values(result.checks).every(Boolean))throw new Error('A runtime lifetime cycle failed');
    }
    result.checks.three_distinct_runtime_cycles=result.runtime_cycles.length===3;
    const peerAfter=(await peerState()).molecular;
    result.checks.independent_camera_and_selection_retained=JSON.stringify(peerAfter.camera_snapshot)===JSON.stringify(peerBefore.camera_snapshot)&&JSON.stringify(peerAfter.active_selection_indices)===JSON.stringify(peerBefore.active_selection_indices);
    result.checks.caller_was_not_reread=hash(callerInput)!==hashes.model&&hash(model)===hashes.model;
  }
  await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,original);
  await page.getByRole('button',{name:'Open'}).first().click();await page.waitForFunction(()=>document.querySelector('[data-testid=reading-text]').textContent.includes('asserted_value'));result.checks.original_source_remains_readable=true;
  await page.screenshot({path:path.join(output,'renderer.png')});fs.writeFileSync(path.join(output,'capture-request'),'capture');await until(()=>fs.existsSync(path.join(output,'native.png'))&&fs.statSync(path.join(output,'native.png')).size>1000,'native composition');result.checks.native_capture=true;
  result.checks.original_inputs_unchanged=hash(card)===hashes.card&&hash(model)===hashes.model;result.input_sha256=hashes;result.checks.no_script_errors=!result.errors.length;
  if(!Object.values(result.checks).every(Boolean))throw new Error('A selected product check failed');result.state='passed';
}catch(error){result.state='failed';result.errors.push(String(error));if(browser)try{const p=browser.contexts()[0].pages()[0];result.failure=await p.evaluate(async()=>({text:document.body.innerText,molecular:await(await fetch('/api/molecular')).json()}));await p.screenshot({path:path.join(output,'failure.png')});}catch{}}
finally{
  if(independentBrowser)await independentBrowser.close();if(browser)await browser.close();for(const child of [...children].reverse()){if(child.exitCode!==null||child.signalCode!==null)continue;child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),delay(10000)]);if(child.exitCode===null&&child.signalCode===null)child.kill('SIGKILL');}for(const log of logs)fs.closeSync(log);
  fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));if(result.state!=='passed')process.exitCode=1;
}
