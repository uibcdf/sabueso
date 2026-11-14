// Actual product receiving through Qt's renderer and native QWidget capture.
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';
import {connectNative} from './standalone_probe/cdp_driver.mjs';
const args=process.argv.slice(2), option=name=>{const index=args.indexOf(name);return index<0?undefined:args[index+1];};
const output=path.resolve(option('--output')),card=path.resolve(option('--deck'));
fs.mkdirSync(output,{recursive:false});
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const before=hash(card), children=[],logs=[];
const result={format:'sabueso.deck_explorer_journey@1',scope:'Actual Qt Deck/Card/source/return product slice; owned Linux Xvfb software request; no molecular/native-platform qualification',checks:{},errors:[]};
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
  launch(option('--python')||'python',['-m','sabueso.explorer',...(args.includes('--empty')?[]:[args.includes('--reading')?'--reading':'--deck',card]),'--output-directory',path.join(output,'readings'),'--debug-port',String(port),'--capture-directory',output],'application',env);
  await until(async()=>{try{browser=await connectNative(`http://127.0.0.1:${port}`);return true;}catch{return false;}},'actual Qt application');
  const page=browser.contexts()[0].pages()[0];page.on('pageerror',error=>result.errors.push(String(error)));
  if(args.includes('--empty')){await page.waitForFunction(()=>!!document.querySelector('.welcome button:not(:disabled)'));result.checks.empty_entry_visible=true;const {root}=await page.send('DOM.getDocument');const {nodeId}=await page.send('DOM.querySelector',{nodeId:root.nodeId,selector:'input[type=file]'});await page.send('DOM.setFileInputFiles',{nodeId,files:[card]});}
  await page.waitForFunction(()=>!!document.querySelector('[data-view-ref]'),null,{timeout:60000});
  const current=()=>page.evaluate(()=>({ref:document.querySelector('[data-view-ref]').dataset.viewRef,result:document.querySelector('[data-view-ref]').dataset.resultRef,text:document.querySelector('[data-testid="reading-text"]').textContent}));
  if(args.includes('--resume-scientific')){
    const state=()=>page.evaluate(async()=>await(await fetch('/api/panel')).json());
    const resumed=await state();result.checks.independent_startup_is_original=resumed.panel.mode==='saved';
    result.checks.original_publication_and_entry_retained=resumed.panel.title.includes('35189560')&&resumed.panel.deck_context.entry_position===4;
    const before=await current();await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.ref);
    result.checks.exact_scientific_trail_retained=(await state()).panel.items.some(i=>i.label.startsWith('Full original target publication context'));
    await page.getByRole('button',{name:'Return to Deck',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);
    result.checks.exact_filtered_deck_and_occurrences=(await state()).panel.items.every(i=>i.label.includes('P52270'));
    await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===5);
    result.checks.original_deck_history_retained=true;
    result.scope='Actual independent Qt startup from original whole workspace; publication, exact Card trail, repeated Deck occurrence, filtered selection and Deck Back; Linux/Xvfb software only';
  }else if(args.includes('--receive-scientific')){
    const manifest=JSON.parse(fs.readFileSync(option('--manifest'),'utf8'));
    const state=()=>page.evaluate(async()=>await(await fetch('/api/panel')).json());
    async function clickItem(item,related=false){if(!item)throw new Error('Missing original scientific destination');const before=await current();await page.locator('[data-item-ref="'+item.ref+'"] .item-actions button:nth-child('+(related?2:1)+')').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.ref);return await state();}
    async function back(ref){await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(old=>document.querySelector('[data-view-ref]').dataset.viewRef===old,ref);}
    const root=await current();result.checks.five_explicit_input_occurrences=(await state()).panel.items.length===5;
    await page.locator('#search').focus();await page.send('Input.insertText',{text:'protein'});await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);const selected=await state();
    const entry=await clickItem(selected.panel.items[1]);result.checks.repeated_protein_entry=entry.panel.deck_context.entry_position===4;
    await page.locator('#search').focus();await page.send('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await page.send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});await page.send('Input.insertText',{text:'BTS'});await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelector('[data-view-ref] h2').textContent==='Literal search');
    const search=await state(),entity=search.panel.items.find(i=>i.label==='pdb.ligand:BTS');await clickItem(entity,true);const links=await state();
    const ligand=await clickItem(links.panel.items.find(i=>i.label==='Entity · pdb.ligand:BTS'));
    result.checks.source_identity_opens_supplied_ligand=ligand.panel.profile==='small_molecule'&&ligand.panel.deck_context.current_card.card_ref===manifest.cards.ligand.pin;
    result.checks.entry_occurrence_stays_protein=ligand.panel.deck_context.card.card_ref===manifest.cards.protein.pin&&ligand.panel.deck_context.entry_position===4;
    await page.locator('[data-topic="activity_context"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,ligand.panel.view_ref);
    let p=await state();const groups=await clickItem(p.panel.items[0]);const records=await clickItem(groups.panel.items[0]);
    result.checks.original_activity_quantity_has_unit=records.panel.items[0].preview.cells.some(c=>c.quantity?.unit==='nanomolar');
    const context=await clickItem(records.panel.items[0],true),assay=context.panel.items.find(i=>i.label==='Retained original target assay context');
    const assayReading=await clickItem(assay);result.checks.original_assay_context_opens=assayReading.panel.text.includes('CHEMBL5138431');await back(context.panel.view_ref);
    p=await state();const publication=p.panel.items.find(i=>i.label.startsWith('Full original target publication context')&&i.label.includes('35189560'));const paper=await clickItem(publication);
    result.checks.original_full_publication_opens=paper.panel.text.includes('35189560')&&paper.panel.deck_context.current_card.card_ref===manifest.cards.ligand.pin;
    const saveStarted=performance.now();await page.getByRole('button',{name:'Save workspace',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Workspace saved:'),null,{timeout:120000});result.save_workspace_elapsed_s=(performance.now()-saveStarted)/1000;const saved=await state();result.saved_workspace=path.join(output,'readings',saved.workspace_saved_file);
    const reopenStarted=performance.now();await page.getByRole('button',{name:'Reopen workspace',exact:true}).click();await page.waitForFunction(()=>document.querySelector('[role=status]').textContent.includes('Original workspace reopened'),null,{timeout:120000});result.reopen_workspace_elapsed_s=(performance.now()-reopenStarted)/1000;const reopened=await state();
    result.checks.original_publication_and_entry_restore=reopened.panel.mode==='saved'&&reopened.panel.view_ref===paper.panel.view_ref&&reopened.panel.deck_context.entry_position===4;
    await back(context.panel.view_ref);result.checks.original_scientific_back_survives_reopening=true;
    await page.getByRole('button',{name:'Return to Deck',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,selected.panel.view_ref);result.checks.exact_filtered_deck_return=JSON.stringify((await state()).panel.items)===JSON.stringify(selected.panel.items);
    await back(root.ref);result.checks.all_original_occurrences_survive=(await state()).panel.items.length===5;
    result.scope='Actual Qt public P52270 to source-bound BTS identity, native activity quantity, original assay/full publication, whole workspace reopening and exact repeated Deck entry return; Linux/Xvfb software only';
  }else if(args.includes('--saved-workspace')){
    const state=()=>page.evaluate(async()=>await(await fetch('/api/panel')).json());
    const read=await state();
    if(args.includes('--reading')){
      result.checks.independent_startup_is_original=read.panel.mode==='saved'&&read.panel.workspace==='deck';
      result.checks.independent_startup_retains_metadata=read.panel.title==='Original Deck metadata'&&read.panel.text.includes('MONDO');
      await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);
      result.checks.independent_startup_retains_selection=true;
      await page.getByRole('button',{name:'Overview'}).click();await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===3);
    }
    const root=await current();result.checks.three_original_occurrences=(await state()).panel.items.length===3;
    await page.getByRole('button',{name:'Order by identifier'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,root.ref);const ordered=await current();
    await page.locator('#search').focus();await page.send('Input.insertText',{text:'0001444'});await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);const selected=await state();
    await page.getByRole('button',{name:'Original membership and metadata'}).click();await page.waitForFunction(()=>document.querySelector('h2').textContent!==''&&document.querySelector('[data-testid="reading-text"]').textContent.includes('MONDO'));const metadata=await state();
    await page.getByRole('button',{name:'Save Deck reading'}).click();await page.waitForFunction(()=>document.querySelector('[role="status"]').textContent.includes('Deck reading saved:'));
    const saved=await state(),file=path.join(output,'readings',saved.panel.saved_file);result.saved_file=file;result.saved_sha256=hash(file);
    result.checks.saved_scope_explicit=await page.evaluate(()=>document.querySelector('[role="status"]').textContent.includes('molecular scene are not included'));
    await page.getByRole('button',{name:'Reopen saved'}).click();await page.waitForFunction(()=>document.querySelector('[data-view-ref] .eyebrow').textContent==='Original saved reading');
    result.checks.in_place_reopening_preserves_metadata=(await state()).panel.text===metadata.panel.text;
    await page.getByRole('button',{name:'Open reading…'}).click();const {root:dom}=await page.send('DOM.getDocument');const {nodeId}=await page.send('DOM.querySelector',{nodeId:dom.nodeId,selector:'input[type=file]'});const before=(await state()).panel.revision;
    await page.send('DOM.setFileInputFiles',{nodeId,files:[file]});await page.waitForFunction(async revision=>(await(await fetch('/api/panel')).json()).panel.revision!==revision,before);
    const uploaded=await state();result.checks.independent_upload_is_original=uploaded.panel.mode==='saved'&&uploaded.panel.view_ref===metadata.panel.view_ref&&uploaded.panel.text===metadata.panel.text;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);
    result.checks.exact_saved_selection=JSON.stringify((await state()).panel.items)===JSON.stringify(selected.panel.items);
    await page.locator('[data-item-ref="'+selected.panel.items[1].ref+'"] .item-actions button').first().click();await page.waitForFunction(()=>!!document.querySelector('[data-topic="sources"]'));
    result.checks.original_member_occurrence=(await state()).panel.mode==='saved'&&(await state()).panel.deck_context.entry_position===2;
    const member=await current();await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,member.ref);const sources=await current();await page.getByRole('button',{name:'Open'}).first().click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sources.ref);
    result.checks.original_source_readable=(await current()).text.includes('asserted_value');
    await page.getByRole('button',{name:'Return to Deck'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,selected.panel.view_ref);result.checks.exact_saved_deck_return=true;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,ordered.ref);result.checks.original_ordered_back=true;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,root.ref);result.checks.original_root_back=(await state()).panel.items.length===3;
    result.checks.saved_file_unchanged=hash(file)===result.saved_sha256;
    result.scope='Actual Qt original Deck save/reopen and independent file upload/startup; exact metadata, repeated occurrences, source and Back; Linux/Xvfb software only';
  }else if(args.includes('--cross-member')){
    const manifest=JSON.parse(fs.readFileSync(option('--manifest'),'utf8')),parentPin=manifest.members[0],childPin=manifest.members[2];
    const state=()=>page.evaluate(async()=>await(await fetch('/api/panel')).json());
    async function clickItem(item,related=false){const before=await current();await page.locator('[data-item-ref="'+item.ref+'"] .item-actions button:nth-child('+(related?2:1)+')').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.ref);}
    async function parentRoute(){const before=await current();await page.locator('[data-topic="classification"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.ref);const classification=await state();const row=classification.panel.items.find(i=>i.label.includes('mondo:MONDO:0000940'));if(!row)throw new Error('Missing source-declared parent row');await clickItem(row,true);const links=await state();await clickItem(links.panel.items.find(i=>i.label.startsWith('Object')&&i.label.includes('mondo:MONDO:0000940')));return {classification,links};}
    const root=await current();result.checks.three_distinct_occurrences=(await state()).panel.items.length===3;
    await page.getByRole('button',{name:'Order by identifier'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,root.ref);const ordered=await current();
    await page.locator('#search').focus();await page.send('Input.insertText',{text:'0001444'});await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);const selected=await state();
    await clickItem(selected.panel.items[1]);const entry=await state();result.checks.repeated_entry_is_explicit=entry.panel.deck_context.entry_position===2&&await page.evaluate(()=>document.querySelector('[data-testid="deck-entry"]').textContent.includes('occurrence 3'));
    const route=await parentRoute(),destination=await state();
    result.checks.source_declared_parent_opens_supplied_card=destination.panel.deck_context.current_card.card_ref===parentPin;
    result.checks.entry_and_current_card_stay_distinct=destination.panel.deck_context.card.card_ref===childPin&&destination.panel.deck_context.entry_position===2&&destination.panel.deck_context.member_ref===entry.panel.deck_context.member_ref;
    await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,destination.panel.view_ref);const sources=await state();await clickItem(sources.panel.items[0]);
    result.checks.destination_owns_original_source=(await current()).text.includes('asserted_value')&&(await state()).panel.deck_context.current_card.card_ref===parentPin;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,sources.panel.view_ref);await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,destination.panel.view_ref);
    result.checks.exact_destination_source_return=true;
    await page.getByRole('button',{name:'Save reading'}).click();await page.waitForFunction(()=>document.querySelector('[role="status"]').textContent.includes('captured Cards saved'));result.checks.saved_scope_is_explicit=true;
    await page.getByRole('button',{name:'Reopen saved'}).click();await page.waitForFunction(()=>document.querySelector('[data-view-ref] .eyebrow').textContent==='Original saved reading');
    result.checks.original_related_reading_reopens=(await state()).panel.deck_context.current_card.card_ref===parentPin&&(await state()).panel.deck_context.entry_position===2;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,destination.panel.view_ref);await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,route.links.panel.view_ref);
    result.checks.exact_cross_card_back=true;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,route.classification.panel.view_ref);
    const missing=(await state()).panel.items.find(i=>i.label.includes('mondo:MONDO:0100120'));await clickItem(missing,true);await clickItem((await state()).panel.items.find(i=>i.label.startsWith('Object')&&i.label.includes('mondo:MONDO:0100120')));
    const unavailable=await state();result.checks.unsupplied_parent_stays_unknown=unavailable.panel.outcome.status==='context_not_supplied'&&unavailable.panel.deck_context.current_card.card_ref===null;
    await page.getByRole('button',{name:'Return to Deck'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,selected.panel.view_ref);result.checks.exact_filtered_deck_return=JSON.stringify((await state()).panel.items)===JSON.stringify(selected.panel.items);
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,ordered.ref);result.checks.exact_ordered_deck_return=true;
    await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,root.ref);result.checks.original_occurrences_retained=(await state()).panel.items.length===3;
    await clickItem((await state()).panel.items[2]);await parentRoute();result.scope='Actual Qt public MONDO child/parent/source/original-save/exact-Deck return, plus unsupplied-context control; Linux/Xvfb software only';
  }else{
  const root=await current();
  result.checks.three_distinct_occurrences=await page.evaluate(()=>document.querySelectorAll('.items .item').length===3);
  await page.getByRole('button',{name:'Order by nature'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,root.ref);
  const ordered=await current();
  await page.locator('#search').focus();await page.send('Input.insertText',{text:'protein'});await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);
  const selected=await current();result.checks.literal_member_filter=true;
  await page.getByRole('button',{name:'Open'}).first().click();await page.waitForFunction(()=>!!document.querySelector('[data-topic="sources"]'));
  result.checks.card_opened_from_selected_occurrence=true;
  const sourceList=await current();await page.locator('[data-topic="sources"]').click();
  await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sourceList.ref);
  const sourceReady=await current();await page.getByRole('button',{name:'Open'}).first().click();
  await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sourceReady.ref);
  result.checks.original_source_opened=(await current()).text.includes('asserted_value');
  await page.getByRole('button',{name:'Return to Deck'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,selected.ref);
  result.checks.exact_filtered_deck_return=true;
  await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,ordered.ref);
  result.checks.exact_ordered_deck_return=true;
  await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,root.ref);
  await page.getByRole('button',{name:'Original membership and metadata'}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="reading-text"]').textContent.includes('Synthetic application control'));
  result.checks.original_metadata_inspectable=true;
  await page.getByRole('button',{name:'Back'}).click();await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===3);
  result.checks.metadata_back_preserves_members=true;
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
