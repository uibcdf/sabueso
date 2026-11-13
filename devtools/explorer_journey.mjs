// Actual product receiving through Qt's renderer and native QWidget capture.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {connectNative} from './standalone_probe/cdp_driver.mjs';
const args=process.argv.slice(2), option=name=>args[args.indexOf(name)+1];
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
  launch(option('--python')||'python',['-m','sabueso.explorer',...(args.includes('--empty')?[]:['--card',card]),'--output-directory',path.join(output,'readings'),'--debug-port',String(port),'--capture-directory',output],'application',env);
  await until(async()=>{try{browser=await connectNative(`http://127.0.0.1:${port}`);return true;}catch{return false;}},'actual Qt application');
  const page=browser.contexts()[0].pages()[0];page.on('pageerror',error=>result.errors.push(String(error)));
  if(args.includes('--empty')){await page.waitForFunction(()=>!!document.querySelector('.welcome button:not(:disabled)'));result.checks.empty_entry_visible=true;const {root}=await page.send('DOM.getDocument');const {nodeId}=await page.send('DOM.querySelector',{nodeId:root.nodeId,selector:'input[type=file]'});await page.send('DOM.setFileInputFiles',{nodeId,files:[card]});}
  await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'),null,{timeout:60000});
  const current=()=>page.evaluate(()=>({ref:document.querySelector('[data-view-ref]').dataset.viewRef,result:document.querySelector('[data-view-ref]').dataset.resultRef,text:document.querySelector('[data-testid="reading-text"]').textContent}));
  const original=await current();
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
  await page.screenshot({path:path.join(output,'renderer.png')});
  fs.writeFileSync(path.join(output,'capture-request'),'capture');await until(()=>fs.existsSync(path.join(output,'native.png')) && fs.statSync(path.join(output,'native.png')).size>1000,'native composition capture');
  result.checks.actual_native_capture=fs.statSync(path.join(output,'native.png')).size>1000;
  result.checks.input_unchanged=hash(card)===before;
  result.checks.no_script_errors=result.errors.length===0;
  result.input_sha256=before;result.opened_text_excerpt=opened.text.slice(0,100);
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
