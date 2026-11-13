// Task-scoped page automation. Qt exposes renderer CDP, not full BrowserContext
// management. Use the same small, real Runtime/Page/Input surface in both hosts.
// This driver never emulates a molecular event or accesses Mol* internals.
import fs from 'node:fs';
import {setTimeout as delay} from 'node:timers/promises';

async function until(predicate, timeout = 30000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    try {if (await predicate()) return;} catch (error) {
      if (!String(error).includes('not defined') && !String(error).includes('Cannot read properties')) throw error;
    }
    await delay(100);
  }
  throw new Error('Page condition timed out');
}

class PageDriver {
  constructor(socket) {
    this.socket = socket;
    this.sequence = 0;
    this.pending = new Map();
    this.listeners = new Map();
    this.views = new Map();
    this.keyboard = {press: async key => {
      if (key !== 'Enter') throw new Error('Only the declared Enter action is implemented');
      await this.send('Input.dispatchKeyEvent', {type:'keyDown', key:'Enter', code:'Enter', text:'\r', unmodifiedText:'\r', windowsVirtualKeyCode:13, nativeVirtualKeyCode:13});
      await this.send('Input.dispatchKeyEvent', {type:'keyUp', key:'Enter', code:'Enter', windowsVirtualKeyCode:13});
    }};
    socket.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const call = this.pending.get(message.id);
        if (!call) return;
        clearTimeout(call.timer); this.pending.delete(message.id);
        if (message.error) call.reject(new Error(`${call.method}: ${message.error.message}`));
        else call.resolve(message.result);
      } else this.event(message);
    });
  }
  send(method, params = {}) {
    const id = ++this.sequence;
    return new Promise((resolve,reject) => {
      const timer = setTimeout(() => {this.pending.delete(id); reject(new Error(`CDP timeout: ${method}`));}, 15000);
      this.pending.set(id, {resolve,reject,timer,method});
      this.socket.send(JSON.stringify({id,method,params}));
    });
  }
  frame(id, url) {
    let view = this.views.get(id);
    if (!view) {view = new FrameDriver(this,id,url); this.views.set(id,view);}
    if (url) view.address = url;
    return view;
  }
  event(message) {
    const p = message.params;
    if (message.method === 'Page.frameNavigated') this.frame(p.frame.id,p.frame.url);
    if (message.method === 'Runtime.executionContextCreated' && p.context.auxData?.isDefault) {
      this.frame(p.context.auxData.frameId).contextId = p.context.id;
    }
    if (message.method === 'Runtime.consoleAPICalled') {
      const text = p.args.map(x => x.value ?? x.description ?? '').join(' ');
      for (const callback of this.listeners.get('console') ?? []) callback({type:()=>p.type,text:()=>text});
    }
    if (message.method === 'Runtime.exceptionThrown') {
      const text = p.exceptionDetails.exception?.description ?? p.exceptionDetails.text;
      for (const callback of this.listeners.get('pageerror') ?? []) callback(new Error(text));
    }
    if (message.method === 'Network.requestWillBeSent') {
      for (const callback of this.listeners.get('request') ?? []) callback({url:()=>p.request.url});
    }
  }
  on(name, callback) {
    const callbacks = this.listeners.get(name) ?? []; callbacks.push(callback); this.listeners.set(name,callbacks);
  }
  async evaluateIn(fn, arg, contextId) {
    const result = await this.send('Runtime.evaluate', {expression:`(${fn.toString()})(${JSON.stringify(arg ?? null)})`,
      awaitPromise:true, returnByValue:true, userGesture:true, ...(contextId ? {contextId} : {})});
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text);
    return result.result.value;
  }
  evaluate(fn,arg) {return this.evaluateIn(fn,arg,this.main.contextId);}
  waitForFunction(fn,arg,options) {return until(()=>this.evaluate(fn,arg), options?.timeout ?? 30000);}
  frames() {return [...this.views.values()];}
  mainFrame() {return this.main;}
  locator(selector) {return new ElementDriver(this.main,selector);}
  getByRole(role,{name}) {
    if (role !== 'button') throw new Error('Only declared button actions are implemented');
    return new ElementDriver(this.main,'button',name);
  }
  async screenshot({path}) {
    const result = await this.send('Page.captureScreenshot', {format:'png',captureBeyondViewport:false});
    fs.writeFileSync(path, Buffer.from(result.data,'base64'));
  }
}

class FrameDriver {
  constructor(page,id,url) {this.page=page;this.id=id;this.address=url;}
  url() {return this.address;}
  evaluate(fn,arg) {return this.page.evaluateIn(fn,arg,this.contextId);}
  locator(selector) {return new ElementDriver(this,selector);}
}

class ElementDriver {
  constructor(frame,selector,name) {this.frame=frame;this.selector=selector;this.name=name;}
  first() {return this;}
  async evaluate(fn) {
    const find = `[...document.querySelectorAll(${JSON.stringify(this.selector)})].find(x=>${this.name ? `x.textContent.trim()===${JSON.stringify(this.name)}` : 'true'})`;
    return this.frame.page.evaluateIn(`() => (${fn.toString()})(${find})`, null, this.frame.contextId);
  }
  async boundingBox() {
    const rect = await this.evaluate(element=>{const r=element.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};});
    if (this.frame !== this.frame.page.main) {
      const parent = await this.frame.page.locator('[data-testid="molecular-frame"]').boundingBox();
      rect.x += parent.x; rect.y += parent.y;
    }
    return rect;
  }
  waitFor() {return until(async()=>{const r=await this.boundingBox();return r.width>0 && r.height>0;});}
  async focus() {await this.evaluate(element=>element.focus());}
  async click({position} = {}) {
    await this.evaluate(element=>element.scrollIntoView({block:'nearest',inline:'nearest'}));
    const box = await this.boundingBox();
    const x = box.x+(position?.x ?? box.width/2), y=box.y+(position?.y ?? box.height/2);
    await this.frame.page.send('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});
    await this.frame.page.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});
    await this.frame.page.send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});
  }
}

export async function connectNative(endpoint) {
  const targets = await (await fetch(`${endpoint}/json/list`)).json();
  const target = targets.find(x=>x.type==='page');
  if (!target) throw new Error('No native renderer page is exposed');
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  const page = new PageDriver(socket);
  await page.send('Page.enable');
  await page.send('Runtime.enable');
  await page.send('Network.enable');
  const {frameTree} = await page.send('Page.getFrameTree');
  function register(tree) {page.frame(tree.frame.id,tree.frame.url);for(const child of tree.childFrames ?? []) register(child);}
  register(frameTree); page.main=page.views.get(frameTree.frame.id);
  return {contexts:()=>[{pages:()=>[page]}], close:async()=>{socket.close();}};
}
