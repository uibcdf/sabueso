// Actual Qt source/Back position receiving. Scientific views remain native.
import {setTimeout as delay} from 'node:timers/promises';

export async function receivePosition(page,result){
  const state=async()=>(await page.evaluate(async()=>await(await fetch('/api/panel')).json())).panel;
  const before=await state();await page.locator('[data-topic="sources"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.view_ref);
  const sources=await state(),item=sources.items[Math.min(5,sources.items.length-1)];
  if(!item)throw new Error('Position receiving needs retained original statements');
  const target=page.locator('[data-item-ref="'+item.ref+'"] .item-actions button');
  const position=()=>page.evaluate(()=>{const root=document.querySelector('[data-view-ref]'),active=document.activeElement;return {top:root.scrollTop,left:root.scrollLeft,focused_item:active?.closest('[data-item-ref]')?.getAttribute('data-item-ref')??null,heading_focused:active===root.querySelector('.reading-title'),reading_focused:active===root};});
  await target.focus();await delay(120);const parent=await position();
  result.position={source_item_ref:item.ref,parent_view_ref:sources.view_ref,parent};
  result.checks.position_control_is_scrolled_parent=parent.top>20&&parent.focused_item===item.ref;
  await page.keyboard.press('Enter');await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sources.view_ref);await delay(120);
  const child=await state(),opened=await position();result.position.opened=opened;
  result.checks.new_reading_starts_at_top=opened.top<=1;
  result.checks.new_reading_focuses_heading=opened.heading_focused;
  await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,sources.view_ref);await delay(120);
  const returned=await state(),restored=await position();result.position.restored=restored;
  result.checks.back_restores_parent_scroll=Math.abs(restored.top-parent.top)<=3&&Math.abs(restored.left-parent.left)<=1;
  result.checks.back_restores_original_item_focus=restored.focused_item===item.ref;
  result.checks.position_return_keeps_native_reading=returned.result_ref===sources.result_ref&&returned.text===sources.text;
  await target.focus();await page.keyboard.press('Enter');await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,child.view_ref);await delay(120);
  const repeated=await position();result.position.repeated=repeated;
  result.checks.new_visit_is_not_a_stale_scroll_return=repeated.top<=1&&repeated.heading_focused;
  result.checks.position_preserves_exact_child=(await state()).text===child.text;

  await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,sources.view_ref);
  if((await state()).has_next){
    await page.getByRole('button',{name:'Next page',exact:true}).click();await page.waitForFunction(async()=>((await(await fetch('/api/panel')).json()).panel.offset)>0);await delay(120);
    const second=await state(),pageItem=second.items[Math.min(5,second.items.length-1)],pageTarget=page.locator('[data-item-ref="'+pageItem.ref+'"] .item-actions button');
    result.checks.page_change_starts_at_heading=(await position()).top<=1&&(await position()).heading_focused;
    await pageTarget.focus();await delay(120);const secondPosition=await position();await page.keyboard.press('Enter');await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,second.view_ref);
    await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,second.view_ref);await delay(120);
    const restoredPage=await state(),atPage=await position();result.position.page={offset:second.offset,before:secondPosition,after:atPage};
    result.checks.page_bound_return_keeps_exact_offset=restoredPage.offset===second.offset&&restoredPage.result_ref===second.result_ref&&restoredPage.text===second.text;
    result.checks.page_bound_return_keeps_position_and_control=Math.abs(atPage.top-secondPosition.top)<=3&&atPage.focused_item===pageItem.ref;
  }

  // Hold one actual response unchanged to exercise the focus race, not latency.
  const prior=await state();
  await page.evaluate(()=>{
    const original=window.fetch;let armed=true,release;const gate=new Promise(resolve=>{release=resolve;});
    window.__positionReceiving={release,seen:false,restore:()=>{window.fetch=original;release();delete window.__positionReceiving;}};
    window.fetch=function(...args){const response=original.apply(this,args);if(armed&&args[0]==='/api/action'){armed=false;return response.then(async result=>{window.__positionReceiving.seen=true;await gate;return result;});}return response;};
  });
  try{
    await page.locator('[data-topic="content"]').click();await page.waitForFunction(()=>window.__positionReceiving.seen);
    await page.locator('#search').focus();await page.send('Input.insertText',{text:'position receiving focus control'});
    await page.evaluate(()=>window.__positionReceiving.release());await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,prior.view_ref);await delay(120);
    result.checks.pending_response_does_not_steal_search_focus=await page.evaluate(()=>document.activeElement===document.querySelector('#search')&&document.querySelector('#search').value==='position receiving focus control');
    result.position.focus_race_scope='One actual native action response held unchanged in the browser; synthetic scheduling, not source/server latency';
  }finally{await page.evaluate(()=>window.__positionReceiving?.restore());}
}

export async function receiveDeckPosition(page,result){
  const state=async()=>(await page.evaluate(async()=>await(await fetch('/api/panel')).json())).panel;
  const outer=await state();
  if(outer.workspace!=='deck'||outer.items.length<3)throw new Error('Repeated-entry receiving needs the declared original three-occurrence Deck');
  const visits=[];
  // The protected original declares repeated child occurrences at positions 1/2.
  for(const index of [1,2]){
    const member=outer.items[index],button=page.locator('[data-item-ref="'+member.ref+'"] .item-actions button');
    await button.focus();await page.keyboard.press('Enter');await page.waitForFunction(()=>!!document.querySelector('[data-testid="deck-entry"]'));await delay(120);
    const card=await state(),initial=await page.evaluate(()=>{const reading=document.querySelector('[data-view-ref]');return {top:reading.scrollTop,heading:document.activeElement===reading.querySelector('.reading-title')};});
    const control=page.locator('.items .item-actions button').first();await control.focus();await delay(120);
    const away=await page.evaluate(()=>document.querySelector('[data-view-ref]').scrollTop);
    visits.push({entry:card.deck_context.entry_position,card_ref:card.deck_context.current_card.card_ref,view_ref:card.view_ref,initial,away});
    await page.getByRole('button',{name:'Return to Deck',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,outer.view_ref);await delay(120);
    result.checks['deck_return_focus_'+index]=await page.evaluate(ref=>document.activeElement?.closest('[data-item-ref]')?.getAttribute('data-item-ref')===ref,member.ref);
  }
  result.position_deck={visits};
  result.checks.repeated_card_positions_use_declared_occurrences=visits[0].card_ref===visits[1].card_ref&&visits[0].view_ref===visits[1].view_ref&&visits[0].entry!==visits[1].entry;
  result.checks.repeated_card_entry_starts_at_top=visits.every(v=>v.initial.top<=1&&v.initial.heading);
  result.checks.deck_position_preserves_outer_reading=(await state()).text===outer.text&&JSON.stringify((await state()).items)===JSON.stringify(outer.items);
}
