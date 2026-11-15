// Real retained-source/title/history receiving; no source or model replacement.
export async function receiveNavigation(page,result){
  const state=async()=>(await page.evaluate(async()=>await(await fetch('/api/panel')).json())).panel;
  const topic=async name=>{const before=await state();await page.locator('[data-topic="'+name+'"]').click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,before.view_ref);return state();};
  const sources=await topic('sources');
  const item=[...sources.items].sort((a,b)=>Array.from(b.label).length-Array.from(a.label).length)[0];
  if(!item)throw new Error('Navigation receiving needs a retained source statement');
  await page.locator('[data-item-ref="'+item.ref+'"] .item-actions button').first().click();
  await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef!==ref,sources.view_ref);
  const source=await state(),long=await page.evaluate(expected=>document.querySelector('.reading-title').textContent!==expected,source.title);
  result.navigation={source_title:source.title,source_view_ref:source.view_ref,source_result_ref:source.result_ref,long_title:long};
  result.checks.heading_retains_exact_full_title=await page.evaluate(expected=>document.querySelector('.reading-title').getAttribute('title')===expected,source.title);
  if(long){
    result.checks.heading_is_compact=await page.evaluate(expected=>document.querySelector('.reading-title').textContent!==expected,source.title);
    await page.locator('.reading-title-disclosure>summary').focus();await page.keyboard.press('Enter');
    result.checks.full_title_opens_with_keyboard=await page.evaluate(expected=>document.querySelector('.reading-title-disclosure').open&&document.querySelector('.reading-title-disclosure p').textContent===expected,source.title);
  }
  result.navigation.reading_dimensions=await page.evaluate(()=>{const p=document.querySelector('[data-view-ref]');return {width:p.clientWidth,scroll_width:p.scrollWidth};});
  result.checks.reading_needs_no_horizontal_scroll=result.navigation.reading_dimensions.scroll_width<=result.navigation.reading_dimensions.width+1;
  const sourceIndex=source.trail.length;
  for(const name of ['content','sources','content','sources','content','sources','content','sources'])await topic(name);
  const history=await state();
  result.checks.all_exact_history_points_available=await page.evaluate(points=>{
    const buttons=[...document.querySelectorAll('.reading-trail button')];
    return buttons.length===points.length&&points.every(point=>buttons.some(button=>Number(button.dataset.historyIndex)===point.index&&button.getAttribute('aria-label')===point.title));
  },history.trail);
  await page.locator('.earlier-trail>summary').focus();await page.keyboard.press('Enter');
  result.checks.earlier_history_opens_with_keyboard=await page.evaluate(()=>document.querySelector('.earlier-trail').open);
  const target=page.locator('.earlier-trail [data-history-index="'+sourceIndex+'"]');
  await target.focus();await page.keyboard.press('Enter');
  await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,source.view_ref);
  const returned=await state();
  result.checks.earlier_return_preserves_exact_occurrence=returned.result_ref===source.result_ref&&returned.title===source.title&&returned.trail.length===sourceIndex;
  await page.getByRole('button',{name:'Back',exact:true}).click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,sources.view_ref);
  result.checks.earlier_source_parent_back_is_exact=(await state()).result_ref===sources.result_ref;
  await page.locator('[data-item-ref="'+item.ref+'"] .item-actions button').first().click();await page.waitForFunction(ref=>document.querySelector('[data-view-ref]').dataset.viewRef===ref,source.view_ref);
  const final=await state();
  result.checks.native_reading_is_unchanged=final.text===source.text&&final.view_ref===source.view_ref&&final.result_ref===source.result_ref;
  result.checks.disclosure_resets_on_new_reading=await page.evaluate(()=>!document.querySelector('.reading-title-disclosure')?.open);
}
