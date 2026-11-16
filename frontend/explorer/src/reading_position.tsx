import {useLayoutEffect,useRef} from 'react';

type Point={result_ref:string;view_ref:string;workspace?:string;deck_context?:{entry_position:number;current_card?:{card_ref:string}};offset:number;full_text?:{offset:number}|null;trail?:unknown[]};
export type ReadingIntent='visit'|'return'|'stay'|'reset';
type Focus={control:string;item:string|null;column:string|null;field:string|null;history:string|null};
type Position={top:number;left:number;focus:Focus|null};

function keyOf(point:Point){return JSON.stringify([point.result_ref,point.view_ref,point.workspace??'card',point.deck_context?.entry_position??null,point.deck_context?.current_card?.card_ref??null,point.offset,point.full_text?.offset??null,point.trail?.length??null]);}
function address(element:Element|null,root:HTMLElement):Focus|null{
  if(!element||!root.contains(element))return null;
  const target=element.closest<HTMLElement>('[data-reading-control]');
  if(!target)return null;
  return {control:target.dataset.readingControl!,item:target.closest('[data-item-ref]')?.getAttribute('data-item-ref')??null,column:target.closest('[data-column]')?.getAttribute('data-column')??null,field:target.dataset.readingField??null,history:target.dataset.historyIndex??null};
}
function find(root:HTMLElement,focus:Focus|null){
  if(!focus)return null;
  if(focus.control==='reading')return root;
  return Array.from(root.querySelectorAll<HTMLElement>('[data-reading-control]')).find(element=>{
    const candidate=address(element,root);
    return candidate&&Object.keys(focus).every(key=>candidate[key as keyof Focus]===focus[key as keyof Focus]);
  })??null;
}
function visible(element:HTMLElement,root:HTMLElement){
  const box=element.getBoundingClientRect(),viewport=root.getBoundingClientRect();
  return !!element.getClientRects().length&&!element.matches(':disabled')&&box.bottom>viewport.top&&box.top<viewport.bottom&&box.right>viewport.left&&box.left<viewport.right;
}

/** Transient presentation only; no native or saved-reading state is modified. */
export class ReadingPositionMemory{
  private points=new Map<string,Position>();
  private attached:{root:HTMLElement;key:string}|null=null;
  version=0;
  intent:{key:string;kind:ReadingIntent;origin:Element|null|undefined;focus:boolean}|null=null;

  prepare(point:Point|null,kind:ReadingIntent,origin?:Element|null){
    this.version++;
    if(kind==='reset')this.points.clear();
    if(!point){this.intent=null;return;}
    const key=keyOf(point);
    if(kind==='visit')this.points.delete(key);
    this.intent={key,kind,origin,focus:kind!=='stay'&&origin!==undefined};
  }
  captureCurrent(){if(this.attached?.root.isConnected)this.remember(this.attached.root,this.attached.key);}
  remember(root:HTMLElement,key:string){
    const focus=address(document.activeElement,root)??this.points.get(key)?.focus??null;
    this.points.delete(key);this.points.set(key,{top:root.scrollTop,left:root.scrollLeft,focus});
    while(this.points.size>256)this.points.delete(this.points.keys().next().value!);
  }
  attach(root:HTMLElement,key:string){this.attached={root,key};}
  detach(root:HTMLElement){if(this.attached?.root===root)this.attached=null;}
  read(key:string){return this.points.get(key);}
}

export function useReadingPosition(point:Point,memory:ReadingPositionMemory){
  const ref=useRef<HTMLElement>(null),key=keyOf(point),version=memory.version;
  useLayoutEffect(()=>{
    const root=ref.current;if(!root)return;
    const position=memory.read(key),intent=memory.intent;
    memory.attach(root,key);
    root.scrollTop=position?.top??0;root.scrollLeft=position?.left??0;
    const remember=()=>memory.remember(root,key);
    root.addEventListener('scroll',remember,{passive:true});root.addEventListener('focusin',remember);
    const frame=requestAnimationFrame(()=>{
      if(!root.isConnected||memory.version!==version)return;
      const active=document.activeElement,allowed=intent?.focus&&(active===intent.origin||active===document.body||active===null);
      if(allowed){
        const target=position?find(root,position.focus):root.querySelector<HTMLElement>('.reading-title');
        (target&&visible(target,root)?target:root).focus({preventScroll:true});
      }
      if(intent===memory.intent&&intent){intent.focus=false;intent.origin=undefined;}
      remember();
    });
    return()=>{cancelAnimationFrame(frame);root.removeEventListener('scroll',remember);root.removeEventListener('focusin',remember);memory.detach(root);};
  },[key,version,memory]);
  return ref;
}
