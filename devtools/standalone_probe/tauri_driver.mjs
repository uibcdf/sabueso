// Task-only embedded WebDriver for observation; native XTest for actual input.
// The diagnostic script observes standard browser APIs in the cross-origin frame.
import fs from 'node:fs';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {setTimeout as delay} from 'node:timers/promises';
const execute = promisify(execFile);
const here = path.dirname(fileURLToPath(import.meta.url));
async function until(fn, timeout=30000) {
  const end=Date.now()+timeout;
  while(Date.now()<end) {if(await fn()) return; await delay(100);}
  throw new Error('Tauri page condition timed out');
}
class TauriPage {
  constructor(endpoint,id,python,env) {
    this.endpoint=`${endpoint}/session/${id}`;this.python=python;this.env=env;
    this.main={url:()=>this.address};
    this.molecular={url:()=>this.frameAddress,locator:()=>new TauriElement(this,null,null,true)};
    this.keyboard={press:async key=>{if(key!=='Enter')throw new Error('Undeclared key');await this.input({kind:'enter'});}};
  }
  async call(method,route,body) {
    const response=await fetch(this.endpoint+route,{method,signal:AbortSignal.timeout(20000),
      ...(body?{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
    const result=await response.json();
    if(!response.ok || result.value?.error) throw new Error(`WebDriver ${route}: ${JSON.stringify(result.value)}`);
    return result.value;
  }
  async evaluate(fn,arg) {
    const result=await this.call('POST','/execute/async',{script:
      `const done=arguments[arguments.length-1]; Promise.resolve((${fn.toString()})(arguments[0]))`+
      `.then(value=>done({ok:true,value:value??null}),error=>done({ok:false,error:String(error)}));`,args:[arg??null]});
    if(!result.ok)throw new Error(result.error);
    return result.value;
  }
  async waitForFunction(fn,arg,options) {
    await until(()=>this.evaluate(fn,arg),options?.timeout??30000);
    this.frameAddress=await this.evaluate(()=>document.querySelector('[data-testid="molecular-frame"]')?.src);
    this.address=await this.evaluate(()=>location.href);
  }
  locator(selector){return new TauriElement(this,selector);}
  getByRole(role,{name}) {if(role!=='button')throw new Error('Undeclared role');return new TauriElement(this,'button',name);}
  mainFrame(){return this.main;}
  frames(){return [this.main,this.molecular];}
  on(){} // Browser failures/resources are captured by the explicit all-frame observer.
  async input(event) {
    await execute(this.python,[path.join(here,'x11_input.py'),JSON.stringify({...event,display:this.env.DISPLAY})],{env:this.env});
  }
  async screenshot({path}) {
    const png=await this.call('GET','/screenshot');fs.writeFileSync(path,Buffer.from(png,'base64'));
  }
}
class TauriElement {
  constructor(page,selector,name,canvas=false){this.page=page;this.selector=selector;this.name=name;this.canvas=canvas;}
  first(){return this;}
  async evaluate(fn){
    if(this.canvas)throw new Error('Use the explicit frame diagnostics for the cross-origin canvas');
    return this.page.evaluate(({selector,name,code})=>{
      const element=[...document.querySelectorAll(selector)].find(x=>!name || x.textContent.trim()===name);
      return (0,eval)(`(${code})`)(element);
    },{selector:this.selector,name:this.name,code:fn.toString()});
  }
  async boundingBox(){
    if(!this.canvas)return this.evaluate(element=>{const r=element.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};});
    const box=await this.page.locator('[data-testid="molecular-frame"]').boundingBox();
    const inner=await this.page.evaluate(()=>window.__sabuesoObservedFrame?.canvas_rect);
    return inner?{x:box.x+inner.x,y:box.y+inner.y,width:inner.width,height:inner.height}:null;
  }
  async waitFor(){await until(async()=>{const r=await this.boundingBox();return r?.width>0 && r?.height>0;});}
  async focus(){await this.evaluate(element=>element.focus());}
  async click({position}={}) {
    if(!this.canvas)await this.evaluate(element=>element.scrollIntoView({block:'nearest',inline:'nearest'}));
    const r=await this.boundingBox();
    await this.page.input({kind:'click',x:r.x+(position?.x??r.width/2),y:r.y+(position?.y??r.height/2)});
  }
}
export async function connectTauri(endpoint,python,env){
  const response=await fetch(endpoint+'/session',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({capabilities:{alwaysMatch:{}}})});
  const result=await response.json();const id=result.value?.sessionId;
  if(!response.ok || !id)throw new Error(`Tauri WebDriver session failed: ${JSON.stringify(result)}`);
  const page=new TauriPage(endpoint,id,python,env);
  return{contexts:()=>[{pages:()=>[page]}],close:async()=>{
    // Close the real native window so WebKit can dispose its child processes.
    // The loopback server may disappear before returning its final response.
    try {await page.call('DELETE','/window');} finally {await delay(1500);}
  }};
}
