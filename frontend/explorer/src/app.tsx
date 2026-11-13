import {createContext, useContext, useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {DockviewReact, themeLight, type DockviewApi, type DockviewReadyEvent, type SerializedDockview} from 'dockview-react';
import 'dockview-react/dist/styles/dockview.css';
import './style.css';

type Panel={workspace?:'deck';deck_context?:{scope:'entry_occurrence';entry_position:number};revision:string;title:string;text:string;mode:string;profile:string;result_ref:string;view_ref:string;
  topics:{name:string;description:string;availability?:string}[];items:{ref:string;label:string;kind:string}[];
  offset:number;count:number;has_previous:boolean;has_next:boolean;can_back:boolean;can_save:boolean;can_related:boolean;
  full_text:null|{text:string;offset:number;count:number;has_previous:boolean;has_next:boolean};saved_file:string|null;outcome:{status:string;reason?:string}};
type Resolution={revision:string;kind:string;query:string;status:string;entity_ref:string|null;has_card:boolean;choices:{ref:string;entity_ref:string}[];original_text:string};
type Molecular={status:string;error:string|null;initial_file_name:string;initial_input_digest:string;client_url:string|null;correspondence:'not_established';initial_renderer_ready:boolean|null;initial_structure_received:boolean|null;active_selection_indices:number[]|null};
type Presentation={layout:null|{format:string;renderer:string;workspace:SerializedDockview};error:string|null};
const MolecularContext=createContext<Molecular|null>(null);
type Session={panel:Panel;busy:boolean;act:(name:string,extra?:Record<string,unknown>)=>Promise<void>};
const Context=createContext<Session|null>(null);
function useSession(){return useContext(Context)!;}
async function api(path:string,body?:unknown){
  const response=await fetch(path,{credentials:'same-origin',cache:'no-store',
    ...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
  if(!response.ok){let message=await response.text();try{message=JSON.parse(message).error??message;}catch{}throw new Error(message);}
  return response.json();
}
function preview(text:string){
  const lines=text.split('\n');
  if(lines.at(-1)==='Full values: rows(), native_payload. Start: explorer.topics().' && lines.at(-2)?.startsWith('items()[i]'))return lines.slice(0,-2).join('\n');
  return text;
}
function Reading(){
  const {panel,busy,act}=useSession();
  return <article className="reading" data-view-ref={panel.view_ref} data-result-ref={panel.result_ref}>
    {panel.deck_context&&<p className="deck-entry" data-testid="deck-entry">Deck entry: occurrence {panel.deck_context.entry_position+1}. Return to Deck keeps your original selection.</p>}
    <div className="eyebrow">{panel.mode==='saved'?'Original saved reading':'Captured knowledge'}</div>
    <h2>{panel.title}</h2><pre className="reading-text" data-testid="reading-text">{preview(panel.text)}</pre>
    {panel.full_text&&<section aria-label="Complete retained text"><h3>Complete retained text</h3><pre className="reading-text" data-testid="full-text">{panel.full_text.text}</pre>
      <nav className="pagination" aria-label="Complete text pages"><button disabled={busy||!panel.full_text.has_previous} onClick={()=>void act('text_page',{offset:panel.full_text!.offset-4096})}>Previous text</button>
      <span>{panel.full_text.count} characters · starting at {panel.full_text.offset}</span><button disabled={busy||!panel.full_text.has_next} onClick={()=>void act('text_page',{offset:panel.full_text!.offset+4096})}>Next text</button></nav></section>}
    {panel.items.length>0&&<section aria-label="Explore this reading" className="items">{panel.items.map(item=><div className="item" key={item.ref} data-item-ref={item.ref}>
      <div><span className="kind">{item.kind.replaceAll('_',' ')}</span><strong>{item.label}</strong></div>
      <div className="item-actions"><button disabled={busy} onClick={()=>void act('open',{item_ref:item.ref})}>Open</button>
      <button disabled={busy||!panel.can_related} onClick={()=>void act('related',{item_ref:item.ref})}>Sources / questions</button></div>
    </div>)}</section>}
    <nav className="pagination" aria-label="Reading pages"><button disabled={busy||!panel.has_previous} onClick={()=>void(panel.workspace==='deck'?act('deck_previous'):act('page',{offset:panel.offset-40}))}>Previous page</button>
      <span>{panel.count?`${panel.offset+1}–${panel.offset+panel.items.length} of ${panel.count} items`:'No retained items in this reading'}</span>
      <button disabled={busy||!panel.has_next} onClick={()=>void(panel.workspace==='deck'?act('deck_next'):act('page',{offset:panel.offset+40}))}>Next page</button></nav>
  </article>;
}
function Orientation(){const {panel}=useSession();return <article className="reading orientation"><div className="eyebrow">Your context</div><h2>Explore at your own pace</h2>
  <p>Choose a topic, open an item, or inspect the statements behind it. Back returns to your previous reading.</p>
  <p>These views read retained knowledge. Opening a topic does not refresh sources.</p>
  <h3>Molecular representation</h3><MolecularSummary/>
  <h3>Current scope</h3><p>{panel.profile.replaceAll('_',' ')} · {panel.mode==='saved'?'original saved context':'captured Card context'}</p>
  <p>Missing or unqueried information does not establish a negative scientific result.</p>
  {panel.saved_file&&<p>Last saved reading: <strong>{panel.saved_file}</strong></p>}</article>;}
function MolecularSummary(){const model=useContext(MolecularContext);return model?<><p>Initial model input: {model.initial_file_name}</p><p>Correspondence with this Card: not established.</p>{model.error&&<p role="alert">Molecular preview unavailable: {model.error}</p>}</>:<p>No molecular model is linked in this application session. Your Card remains fully readable.</p>;}
function MolecularView(){const model=useContext(MolecularContext);return <section className="molecular-panel"><div className="molecular-caption"><strong>Experimental molecular preview</strong><span>Correspondence with the current Card: not established.</span>{model&&<span>{model.initial_file_name} · {Array.isArray(model.active_selection_indices)?model.active_selection_indices.length+' selected atoms':'Selection not reported'}</span>}</div>{model?.client_url?<iframe title="Live local molecular model" data-testid="molecular-frame" allow="xr-spatial-tracking" src={model.client_url}/>:<p>Molecular preview unavailable.</p>}</section>;}
const components={reading:Reading,orientation:Orientation,molecular:MolecularView};
function Workspace({panel,busy,act,molecular,presentation,saveLayout,notice}:{panel:Panel;busy:boolean;act:Session['act'];molecular:Molecular|null;presentation:Presentation;saveLayout:(layout:SerializedDockview)=>Promise<void>;notice:(message:string)=>void}){
  const dock=useRef<DockviewApi|null>(null);
  function ready(event:DockviewReadyEvent,restore=true){dock.current=event.api;
    if(restore&&presentation.layout){const state=presentation.layout.workspace;
      if(state.panels.molecular&&!molecular?.client_url)notice('The saved layout needs a molecular panel that is unavailable. Opened the default reading layout; no model was loaded.');
      else try{event.api.fromJSON(state);notice('Presentation layout restored. Knowledge and model state are opened separately.');return;}catch{event.api.clear();notice('The saved presentation could not be restored. Opened the default layout.');}}
    else if(restore&&presentation.error)notice('Saved presentation unavailable: '+presentation.error+' Opened the default layout.');
    event.api.addPanel({id:'reading',component:'reading',title:'Knowledge',renderer:'always'});
    if(molecular?.client_url){event.api.addPanel({id:'molecular',component:'molecular',title:'Molecular model',renderer:'always',position:{referencePanel:'reading',direction:'left'},initialWidth:470});event.api.addPanel({id:'orientation',component:'orientation',title:'Context',position:{referencePanel:'reading',direction:'below'},initialHeight:210});}
    else event.api.addPanel({id:'orientation',component:'orientation',title:'Context',position:{referencePanel:'reading',direction:'right'},initialWidth:300});}
  function floating(){const a=dock.current;if(!a)return;const p=a.getPanel('reading')??a.addPanel({id:'reading',component:'reading',title:'Knowledge',renderer:'always'});a.addFloatingGroup(p,{width:720,height:550,position:{left:90,top:90}});}
  function showModel(){const a=dock.current;if(!a||!molecular?.client_url)return;const p=a.getPanel('molecular')??a.addPanel({id:'molecular',component:'molecular',title:'Molecular model',renderer:'always',position:{referencePanel:'reading',direction:'left'}});p.api.setActive();}
  function floatModel(){showModel();const a=dock.current,p=a?.getPanel('molecular');if(a&&p)a.addFloatingGroup(p,{width:720,height:580,position:{left:45,top:45}});}
  function reset(){const a=dock.current;if(!a)return;const m=a.getPanel('molecular');if(m){const root=a.addGroup({direction:'left'});m.api.moveTo({group:root,position:'center'});const r=a.getPanel('reading')??a.addPanel({id:'reading',component:'reading',title:'Knowledge',renderer:'always'});r.api.moveTo({group:m.api.group,position:'right'});const c=a.getPanel('orientation')??a.addPanel({id:'orientation',component:'orientation',title:'Context'});c.api.moveTo({group:r.api.group,position:'bottom'});}else{a.clear();ready({api:a} as DockviewReadyEvent,false);}}

  return <MolecularContext.Provider value={molecular}><Context.Provider value={{panel,busy,act}}><div className="workspace-tools"><span>Arrange your workspace</span><button disabled={busy} onClick={()=>{if(dock.current)void saveLayout(dock.current.toJSON());}}>Save layout</button>{molecular?.client_url&&<><button onClick={showModel}>Show model</button><button onClick={floatModel}>Float model</button></>}<button onClick={floating}>Float reading</button><button onClick={reset}>Reset layout</button></div>
    <div className="dockview-theme-light dock"><DockviewReact theme={themeLight} components={components} onReady={ready}/></div></Context.Provider></MolecularContext.Provider>;
}
function ResolutionReport({result,busy,choose}:{result:Resolution;busy:boolean;choose:(ref:string)=>Promise<void>}){
  return <section className="resolution-report" aria-label="Source query result"><strong>{result.status.replaceAll('_',' ')}</strong> · {result.query}
    {result.entity_ref&&<p>{result.entity_ref}</p>}
    {!result.has_card&&<p>{result.kind==='pdb'&&result.status==='resolved'?'This is a PDB structure record. Choose a source-declared protein below to query its Card.':'This query did not produce a Card. Any reading below is the previous retained context.'}</p>}
    {result.choices.map(item=><button disabled={busy} key={item.ref} onClick={()=>void choose(item.ref)}>Query {item.entity_ref}</button>)}
    <details><summary>Original resolution, source decisions and acquisition trace</summary><pre>{result.original_text}</pre></details>
  </section>;
}
function App(){
  const [panel,setPanel]=useState<Panel|null>(null),[ready,setReady]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState('Opening your workspace…'),[query,setQuery]=useState(''),[fileMode,setFileMode]=useState<'card'|'deck'|'reading'>('card');
  const file=useRef<HTMLInputElement>(null);
  const [molecular,setMolecular]=useState<Molecular|null>(null);
  const [presentation,setPresentation]=useState<Presentation>({layout:null,error:null});
  const [resolution,setResolution]=useState<Resolution|null>(null),[entryKind,setEntryKind]=useState('uniprot'),[identifier,setIdentifier]=useState(''),[entryOpen,setEntryOpen]=useState(false),[canReturnQuery,setCanReturnQuery]=useState(false);
  useEffect(()=>{let active=true;async function start(){try{
    const token=new URLSearchParams(location.hash.slice(1)).get('token');history.replaceState(null,'',location.pathname);
    if(token)await api('/auth',{token});
    const result=await api('/api/panel');if(active){setPresentation(result.presentation??{layout:null,error:null});setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution??null);setCanReturnQuery(result.can_return_query??false);setReady(true);setMessage('Ready to explore retained knowledge.');}
  }catch(error){if(active)setMessage(String(error));}}void start();return()=>{active=false;};},[]);
  useEffect(()=>{if(!molecular?.client_url)return;let stopped=false,pending=false;const poll=async()=>{if(pending||stopped)return;pending=true;try{const result=await api('/api/molecular');if(!stopped)setMolecular(result.molecular);}catch{}finally{pending=false;}};const timer=setInterval(()=>void poll(),1000);return()=>{stopped=true;clearInterval(timer);};},[molecular?.client_url]);
  async function saveLayout(workspace:SerializedDockview){if(busy)return;setBusy(true);try{const result=await api('/api/layout',{format:'sabueso.presentation_layout@1',renderer:'dockview@8.9.0',workspace});setPresentation(result);setMessage('Presentation layout saved. This does not save Knowledge, query history or the molecular scene.');}catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function act(name:string,extra:Record<string,unknown>={}){if(!panel||busy)return;setBusy(true);setMessage('Opening the requested reading…');
    try{const result=await api('/api/action',{name,revision:panel.revision,...extra});setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution??null);setCanReturnQuery(result.can_return_query??false);setMessage(name==='save'?(panel.deck_context!==undefined?'Card reading and captured Cards saved. Deck membership, selection and layout are not saved in this file.':'Reading saved. Reopen it to inspect the original capture.'):'Ready.');}
    catch(error){setMessage(String(error));try{const current=await api('/api/panel');setPanel(current.panel);setResolution(current.resolution??null);setCanReturnQuery(current.can_return_query??false);}catch{setMessage('The reading service is unavailable. Reopen the application to continue.');}}
    finally{setBusy(false);}}
  async function openFile(selected:File){setBusy(true);try{
    if(selected.size>16*1024**2)throw new Error('This input exceeds the 16 MiB opening limit.');
    const response=await fetch(`/api/${fileMode}`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Sabueso-Revision':panel?.revision??'','X-Sabueso-Resolution':resolution?.revision??''},body:selected});if(!response.ok){const error=await response.json();throw new Error(error.error??'Could not open the Card.');}const result=await response.json();setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution??null);setCanReturnQuery(result.can_return_query??false);setMessage(`${fileMode==='deck'?'Deck':fileMode==='reading'?'Original reading':'Card'} opened. Choose where to explore.`);
    }catch(error){setMessage(String(error));}finally{setBusy(false);if(file.current)file.current.value='';}}
  async function acquire(choice_ref?:string){if(!ready||busy)return;setBusy(true);setMessage('Querying the requested public sources…');
    try{const revisions={revision:panel?.revision??'',resolution_revision:resolution?.revision??''};
      const result=await api(choice_ref?'/api/resolve-choice':'/api/resolve',choice_ref?{...revisions,choice_ref}:{...revisions,kind:entryKind,query:identifier});
      setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution);setCanReturnQuery(result.can_return_query??false);setEntryOpen(false);setMessage(result.resolution.has_card?'Card acquired. Further topic navigation reads this capture without refreshing sources.':'Source query finished. Inspect its outcome and original decision.');
    }catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function returnQuery(){if(busy)return;setBusy(true);try{const result=await api('/api/resolve-back',{revision:panel?.revision??'',resolution_revision:resolution?.revision??''});setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution);setCanReturnQuery(result.can_return_query);setMessage('Returned to the exact retained query and reading. No source was queried.');}catch(error){setMessage(String(error));}finally{setBusy(false);}}
  const entry=<form className="entry-form" aria-label="Query public sources" onSubmit={e=>{e.preventDefault();void acquire();}}>
    <label htmlFor="entry-kind">Start from</label><select id="entry-kind" value={entryKind} disabled={busy} onChange={e=>setEntryKind(e.target.value)}><option value="uniprot">UniProt accession</option><option value="pdb">PDB entry</option><option value="smiles">SMILES</option><option value="disease">Disease identifier</option></select>
    <label htmlFor="entry-query">{entryKind==='smiles'?'Public molecular structure (SMILES)':'Identifier'}</label><input id="entry-query" maxLength={8192} value={identifier} disabled={busy} onChange={e=>setIdentifier(e.target.value)} placeholder={{uniprot:'P52270',pdb:'1TCD',smiles:'CCO',disease:'MONDO:0014221'}[entryKind]}/>
    <button className="primary" disabled={!ready||busy||!identifier.trim()}>Query public sources</button>
    <p className="quiet">{entryKind==='smiles'?'The entered SMILES is sent to PubChem for source-stated identity. UniChem expansion is disabled for this initial query.':entryKind==='disease'?'The disease identifier is sent to MONDO. Disease-name search is not offered yet.':entryKind==='pdb'?'The entry identifier is sent to RCSB PDB. Related proteins are offered for a separate query.':'The accession is sent to UniProt.'} Identity profile only; enrichment is not requested automatically.</p>
  </form>;
  return <><header><div className="brand"><span className="brand-mark">S</span><div><h1>Sabueso</h1><p>Molecular knowledge explorer</p></div></div>
    {canReturnQuery&&<button disabled={busy} onClick={()=>void returnQuery()}>Return to previous query</button>}<button disabled={!ready||busy} onClick={()=>setEntryOpen(!entryOpen)}>New source query</button><button disabled={!ready||busy} onClick={()=>{setFileMode('card');file.current?.click();}}>Open Card…</button><button disabled={!ready||busy} onClick={()=>{setFileMode('deck');file.current?.click();}}>Open Deck…</button><button disabled={!ready||busy} onClick={()=>{setFileMode('reading');file.current?.click();}}>Open reading…</button><input ref={file} type="file" accept={fileMode==='deck'?'.jsonl':fileMode==='reading'?'.json,.gz,.zst,application/json':'.json,application/json'} hidden onChange={e=>{const f=e.target.files?.[0];if(f)void openFile(f);}}/></header>
    <div role="status" className={message.startsWith('Error')?'status error':'status'} aria-live="polite">{message}</div>
    {entryOpen&&panel&&<section className="query-drawer">{entry}</section>}{resolution&&<ResolutionReport result={resolution} busy={busy} choose={ref=>acquire(ref)}/>}
    {!panel?<main className="welcome"><div className="eyebrow">Start an exploration</div><h2>What would you like to learn?</h2>
      <p>Choose an identifier to query public sources, or open a local Card or Deck to explore retained knowledge.</p>{entry}
      <button className="primary" disabled={!ready||busy} onClick={()=>{setFileMode('card');file.current?.click();}}>Open a Card JSON file</button><p className="quiet">Opening files and browsing topics makes no source queries. No account required.</p></main>:
    <main className="application"><aside><div className="eyebrow">{panel.profile.replaceAll('_',' ')} knowledge</div><h2>{panel.workspace==='deck'?'Choose a member':'Choose a topic'}</h2>
      <form onSubmit={e=>{e.preventDefault();void act('search',{text:query});}}><label htmlFor="search">{panel.workspace==='deck'?'Filter member identifiers or natures':'Search retained content'}</label><div className="search"><input id="search" maxLength={512} value={query} onChange={e=>setQuery(e.target.value)} placeholder="A name, annotation, or term"/><button disabled={busy||!query.trim()}>Search</button></div></form>
      <nav className="topics" aria-label="Card topics">{panel.workspace==='deck'&&<><button onClick={()=>void act('metadata')} disabled={busy}>Original membership and metadata</button><button onClick={()=>void act('sort',{column:'label',descending:false})} disabled={busy}>Order by identifier</button><button onClick={()=>void act('sort',{column:'kind',descending:false})} disabled={busy}>Order by nature</button><button onClick={()=>void act('sort',{column:'label',descending:true})} disabled={busy}>Reverse identifier order</button></>}{panel.topics.map(topic=><button key={topic.name} disabled={busy} onClick={()=>void act('topic',{topic:topic.name})} data-topic={topic.name}>
        <strong>{topic.name.replaceAll('_',' ')}</strong><span>{topic.description}</span>{topic.availability==='not_saved'&&<em>Not saved in this original reading</em>}</button>)}</nav></aside>
      <section className="main-reading" aria-label="Knowledge workspace"><nav className="actions" aria-label="Reading navigation"><button disabled={busy||!panel.can_back} onClick={()=>void act('back')}>Back</button><button disabled={busy} onClick={()=>void act('overview')}>Overview</button><span/>{panel.deck_context!==undefined&&<button disabled={busy} onClick={()=>void act('deck')}>Return to Deck</button>}
        <button disabled={busy||!panel.can_save} onClick={()=>void act('save')}>Save reading</button><button disabled={busy||!panel.saved_file} onClick={()=>void act('reopen')}>Reopen saved</button></nav>
        <Workspace panel={panel} busy={busy} act={act} molecular={molecular} presentation={presentation} saveLayout={saveLayout} notice={setMessage}/></section></main>}</>;
}
createRoot(document.getElementById('root')!).render(<App/>);
