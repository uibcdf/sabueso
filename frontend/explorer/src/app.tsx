import {createContext, useContext, useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {DockviewReact, themeLight, type DockviewApi, type DockviewReadyEvent, type SerializedDockview} from 'dockview-react';
import 'dockview-react/dist/styles/dockview.css';
import './style.css';

type PreviewCell={column:string;text:string;state:string;reason:string|null;filterable:boolean;quantity:null|{field:string;unit:string;record:unknown}};
type Preview={cells:PreviewCell[];cell_count:number;complete:boolean};
type Overview={profile:string;fields:{path:string;label:string;state:string;text:string;can_open:boolean;support_state:string;sources:{state:string;text:string}[]}[]};
type Graph={rule:string;scope:string;edges:{item_ref:string;subject_ref:string;predicate:string;object_ref:string}[]};
type Panel={workspace?:'deck';deck_context?:{scope:'entry_occurrence';entry_position:number};revision:string;title:string;text:string;mode:string;profile:string;result_ref:string;view_ref:string;
  topics:{name:string;description:string;availability?:string}[];items:{ref:string;label:string;kind:string;preview?:Preview;query_record?:{reference:string;role:string;kind:string;query:string}|null}[];orientation?:Overview|null;graph?:Graph|null;grain?:string|null;trail?:{index:number;title:string}[];
  offset:number;count:number;has_previous:boolean;has_next:boolean;can_back:boolean;can_save:boolean;can_related:boolean;
  full_text:null|{kind?:'text'|'sequence';text:string;offset:number;count:number;has_previous:boolean;has_next:boolean};saved_file:string|null;outcome:{status:string;reason?:string}};
type QueryJob={ref:string;kind:string;query:string;state:'running'|'ready'|'failed'|'cancelled'|'opened';phase:string;error:string|null;worker_running:boolean;protein_source?:string;original_revision:string;original_resolution_revision:string};
type Resolution={revision:string;kind:string;query:string;status:string;entity_ref:string|null;has_card:boolean;choices:{ref:string;entity_ref:string}[];choice_details?:Record<string,{title:string;context:string[]}>;source_access?:{count:number;outcome_counts?:Record<string,number>;rows:{source:string;operation:string;outcome:string;access:string;source_version:string}[];scope:string};original_text:string};
type Molecular={status:string;error:string|null;initial_file_name:string;initial_input_digest:string;client_url:string|null;correspondence:'not_established';initial_renderer_ready:boolean|null;initial_structure_received:boolean|null;active_selection_indices:number[]|null};
type Presentation={layout:null|{format:string;renderer:string;workspace:SerializedDockview};error:string|null};
const MolecularContext=createContext<Molecular|null>(null);
type Session={panel:Panel;busy:boolean;act:(name:string,extra?:Record<string,unknown>)=>Promise<void>;queryBusy:boolean;queryRecord:(ref:string)=>Promise<void>};
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
function ValueCell({cell,itemRef}:{cell:PreviewCell;itemRef:string}){
  const {busy,act}=useSession();return <div className="value-cell"><span className="cell-label">{cell.column.replaceAll('_',' ')}</span>
    <span className="cell-value">{cell.text}</span><span className="cell-state" title={cell.reason??undefined}>{cell.state.replaceAll('_',' ')}</span>
    {cell.quantity&&<span className="unit-label">{cell.quantity.unit}</span>}
    {cell.filterable&&<button className="cell-filter" disabled={busy} title={'Keep rows with the same '+cell.column} onClick={()=>void act('filter_cell',{item_ref:itemRef,column:cell.column})}>Keep same value</button>}
    {cell.reason&&<span className="cell-reason">{cell.reason}</span>}</div>;
}
function SourceGraph({graph}:{graph:Graph}){
  const {busy,act}=useSession();return <section className="relationship-graph" aria-label="Retained relationship graph"><h3>Retained relationships</h3><p className="quiet">{graph.scope}. Each connection opens its original retained record.</p>
    {graph.edges.map(edge=><div className="graph-edge" key={edge.item_ref}><span className="graph-node">{edge.subject_ref}</span><button disabled={busy} onClick={()=>void act('open',{item_ref:edge.item_ref})}><span aria-hidden="true">→ </span>{edge.predicate.replaceAll('_',' ')}<span aria-hidden="true"> →</span></button><span className="graph-node">{edge.object_ref}</span></div>)}</section>;
}
function Reading(){
  const {panel,busy,act,queryBusy,queryRecord}=useSession(),[display,setDisplay]=useState<'cards'|'table'|'graph'>('cards');
  const [expanded,setExpanded]=useState(true);
  const data=panel.orientation,primary=data?.fields[0],mode=display==='graph'&&!panel.graph?'cards':display;
  return <article className="reading" data-view-ref={panel.view_ref} data-result-ref={panel.result_ref}>
    {panel.deck_context&&<p className="deck-entry" data-testid="deck-entry">Deck entry: occurrence {panel.deck_context.entry_position+1}. Return to Deck keeps your original selection.</p>}
    <div className="eyebrow">{panel.mode==='saved'?'Original saved reading':'Captured knowledge'}</div>
    {!!panel.trail?.length&&<nav className="reading-trail" aria-label="Reading trail">{panel.trail.slice(-5).map(point=><button key={point.index} disabled={busy} onClick={()=>void act('back_to',{history_index:point.index})}>{point.title}</button>)}</nav>}
    <h2>{primary?.state==='retained'?primary.text:panel.title}</h2>
    {data&&<section className="overview-fields" aria-label="Original entity overview">{data.fields.map(field=><div className="overview-field" key={field.path}>
      <span className="cell-label">{field.label}</span><strong>{field.state.startsWith('retained')?field.text:field.state.replaceAll('_',' ')}</strong><span className="cell-state">{field.state.replaceAll('_',' ')}</span>
      <span className="quiet">{field.sources.length?field.sources.map(source=>source.text).join(' · '):field.support_state.replaceAll('_',' ')}</span>
      <button disabled={busy||!field.can_open} onClick={()=>void act('orientation_field',{path:field.path})}>Inspect original field</button></div>)}</section>}
    <details className="original-reading" open={!data&&(!panel.items.length||!!panel.full_text)}><summary>Original reading and scope</summary><pre className="reading-text" data-testid="reading-text">{preview(panel.text)}</pre></details>
    {panel.full_text&&<section aria-label="Complete retained text"><h3>{panel.full_text.kind==='sequence'?'Retained primary sequence':'Complete retained text'}</h3>
      {panel.full_text.kind==='sequence'?<><p className="quiet">Positions below index the retained sequence text. They are not mapped structure or isoform coordinates.</p><div className="sequence-strip" data-testid="sequence-strip">{Array.from({length:Math.ceil(panel.full_text.text.length/60)},(_,i)=><div className="sequence-line" key={i}><span>{panel.full_text!.offset+i*60+1}</span><code>{panel.full_text!.text.slice(i*60,i*60+60).match(/.{1,10}/g)?.join(' ')}</code></div>)}</div></>:<pre className="reading-text" data-testid="full-text">{panel.full_text.text}</pre>}
      <nav className="pagination" aria-label="Complete text pages"><button disabled={busy||!panel.full_text.has_previous} onClick={()=>void act('text_page',{offset:panel.full_text!.offset-4096})}>Previous text</button>
      <span>{panel.full_text.count} characters · starting at {panel.full_text.offset}</span><button disabled={busy||!panel.full_text.has_next} onClick={()=>void act('text_page',{offset:panel.full_text!.offset+4096})}>Next text</button></nav></section>}
    {panel.items.some(item=>item.preview)&&<div className="display-controls" role="group" aria-label="Reading presentation"><button disabled={busy} aria-pressed={mode==='cards'} onClick={()=>setDisplay('cards')}>Cards</button><button disabled={busy} aria-pressed={mode==='table'} onClick={()=>setDisplay('table')}>Table</button>{panel.graph&&<button disabled={busy} aria-pressed={mode==='graph'} onClick={()=>setDisplay('graph')}>Relationship graph</button>}<button disabled={busy} aria-pressed={expanded} onClick={()=>setExpanded(!expanded)}>{expanded?'Compact values':'Show values'}</button></div>}
    {panel.grain&&<p className="quiet">{panel.grain}</p>}
    {mode==='graph'&&panel.graph?<SourceGraph graph={panel.graph}/>:panel.items.length>0&&<section aria-label="Explore this reading" className={'items '+(mode==='table'?'table-items':'')}>
      {panel.items.map(item=><div className="item" key={item.ref} data-item-ref={item.ref}>
        <div className="item-body"><span className="kind">{item.kind.replaceAll('_',' ')}</span><strong>{item.label}</strong>
          {item.preview&&(expanded||mode==='table')&&<><div className="cell-grid">{item.preview.cells.map(cell=><ValueCell key={cell.column} cell={cell} itemRef={item.ref}/>)}</div>{!item.preview.complete&&<p className="quiet">Showing {item.preview.cells.length} of {item.preview.cell_count} fields. Open the item for its complete retained content.</p>}</>}
        </div><div className="item-actions"><button disabled={busy} onClick={()=>void act('open',{item_ref:item.ref})}>Open</button><button disabled={busy||!panel.can_related} onClick={()=>void act('related',{item_ref:item.ref})}>Sources / questions</button>{item.query_record&&<button disabled={busy||queryBusy} title={'Query a fresh record for '+item.query_record.reference+'; keep this original reading'} onClick={()=>void queryRecord(item.ref)}>Query referenced record</button>}</div>
      </div>)}</section>}
    <nav className="pagination" aria-label="Reading pages"><button disabled={busy||!panel.has_previous} onClick={()=>void(panel.workspace==='deck'?act('deck_previous'):act('page',{offset:panel.offset-40}))}>Previous page</button>
      <span>{panel.count?`${panel.offset+1}–${panel.offset+panel.items.length} of ${panel.count} items`:'No retained items in this reading'}</span><button disabled={busy||!panel.has_next} onClick={()=>void(panel.workspace==='deck'?act('deck_next'):act('page',{offset:panel.offset+40}))}>Next page</button></nav>
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
function Workspace({panel,busy,act,queryBusy,queryRecord,molecular,presentation,saveLayout,notice}:{panel:Panel;busy:boolean;act:Session['act'];queryBusy:boolean;queryRecord:Session['queryRecord'];molecular:Molecular|null;presentation:Presentation;saveLayout:(layout:SerializedDockview)=>Promise<void>;notice:(message:string)=>void}){
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

  return <MolecularContext.Provider value={molecular}><Context.Provider value={{panel,busy,act,queryBusy,queryRecord}}><div className="workspace-tools"><span>Arrange your workspace</span><button disabled={busy} onClick={()=>{if(dock.current)void saveLayout(dock.current.toJSON());}}>Save layout</button>{molecular?.client_url&&<><button onClick={showModel}>Show model</button><button onClick={floatModel}>Float model</button></>}<button onClick={floating}>Float reading</button><button onClick={reset}>Reset layout</button></div>
    <div className="dockview-theme-light dock"><DockviewReact theme={themeLight} components={components} onReady={ready}/></div></Context.Provider></MolecularContext.Provider>;
}
function ResolutionReport({result,busy,choose}:{result:Resolution;busy:boolean;choose:(ref:string)=>Promise<void>}){
  return <section className="resolution-report" aria-label="Source query result"><strong>{result.status.replaceAll('_',' ')}</strong> · {result.query}
    {(result as Resolution&{mode?:string}).mode==='saved'&&<p className="quiet">Original saved source-query report. No source was queried by reopening it.</p>}{result.entity_ref&&<p>{result.entity_ref}</p>}
    {!result.has_card&&<p>{result.kind==='pdb'&&result.status==='resolved'?'This is a PDB structure record. Choose a source-declared protein below to query its Card.':'This query did not produce a Card. Any reading below is the previous retained context.'}</p>}
    {result.status==='obsolete'&&<p>This terminology record is obsolete. A declared replacement or consideration can be queried separately; the original term and its meaning are not rewritten.</p>}
    {result.status==='ambiguous'&&<p>No candidate has been selected. A follow-up starts a separate source query and keeps this original ambiguity report. It does not merge candidates or settle their identity.</p>}
    {!!result.choices.length&&<div className="source-choices" aria-label="Explicit source follow-up queries">{result.choices.slice(0,32).map(item=><div className="source-choice" key={item.ref}>
      <strong>{result.choice_details?.[item.ref]?.title??'Source-declared follow-up'}</strong>
      {result.choice_details?.[item.ref]?.context.map((text,index)=><p key={index}>{text}</p>)}
      <button disabled={busy} onClick={()=>void choose(item.ref)}>Query {item.entity_ref}</button>
    </div>)}</div>}
    {result.choices.length>32&&<p>Showing the first 32 supported follow-up queries. The complete original report below retains all candidates and their bases.</p>}
    {result.source_access?.outcome_counts&&<p className="source-outcomes" aria-label="Original source access outcomes">Source access: {Object.entries(result.source_access.outcome_counts).slice(0,8).map(([outcome,count])=>`${outcome.replaceAll('_',' ')}: ${count}`).join(' · ')}. Access observations; coverage and quality retain scientific scope.</p>}
    {!!result.source_access?.rows.length&&<details className="source-access"><summary>Observed source access ({result.source_access.count})</summary><p>{result.source_access.scope}. These are the original query observations, including after reopening; browsing makes no source request.</p><ul>{result.source_access.rows.map((row,index)=><li key={index}><strong>{row.source}</strong>: {row.outcome} · {row.operation} · {row.access} · version {row.source_version}</li>)}</ul>{result.source_access.count>16&&<p>Showing the first 16 observations. All retained records remain in the complete original report below.</p>}</details>}
    <details><summary>Original resolution, source decisions and acquisition trace</summary><pre>{result.original_text}</pre></details>
  </section>;
}
function App(){
  const [panel,setPanel]=useState<Panel|null>(null),[ready,setReady]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState('Opening your workspace…'),[query,setQuery]=useState(''),[fileMode,setFileMode]=useState<'card'|'deck'|'reading'>('card');
  const file=useRef<HTMLInputElement>(null);
  const [molecular,setMolecular]=useState<Molecular|null>(null);
  const [job,setJob]=useState<QueryJob|null>(null),attemptedJobs=useRef(new Set<string>());
  const [workspaceSaved,setWorkspaceSaved]=useState<string|null>(null);
  const queryActive=!!job?.worker_running||job?.state==='running';
  const queryWatch=!!job&&(job.worker_running||job.state==='running'||job.state==='ready');
  const [presentation,setPresentation]=useState<Presentation>({layout:null,error:null});
  const [resolution,setResolution]=useState<Resolution|null>(null),[entryKind,setEntryKind]=useState('uniprot'),[proteinSource,setProteinSource]=useState('identity'),[identifier,setIdentifier]=useState(''),[entryOpen,setEntryOpen]=useState(false),[canReturnQuery,setCanReturnQuery]=useState(false);
  useEffect(()=>{let active=true;async function start(){try{
    const token=new URLSearchParams(location.hash.slice(1)).get('token');history.replaceState(null,'',location.pathname);
    if(token)await api('/auth',{token});
    const result=await api('/api/panel');if(active){setPresentation(result.presentation??{layout:null,error:null});setJob(result.query_job??null);setWorkspaceSaved(result.workspace_saved_file??null);setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution??null);setCanReturnQuery(result.can_return_query??false);setReady(true);setMessage('Ready to explore retained knowledge.');}
  }catch(error){if(active)setMessage(String(error));}}void start();return()=>{active=false;};},[]);
  useEffect(()=>{if(!molecular?.client_url)return;let stopped=false,pending=false;const poll=async()=>{if(pending||stopped)return;pending=true;try{const result=await api('/api/molecular');if(!stopped)setMolecular(result.molecular);}catch{}finally{pending=false;}};const timer=setInterval(()=>void poll(),1000);return()=>{stopped=true;clearInterval(timer);};},[molecular?.client_url]);
  function applyReading(result:any){setWorkspaceSaved(result.workspace_saved_file??null);setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution??null);setCanReturnQuery(result.can_return_query??false);}
  useEffect(()=>{if(!job||!queryWatch)return;let stopped=false,pending=false;
    async function poll(){if(pending||stopped)return;pending=true;try{const response=await api('/api/query');const current:QueryJob|null=response.query_job;if(!current||stopped)return;setJob(current);
      if(current.state==='ready'&&!attemptedJobs.current.has(current.ref)){attemptedJobs.current.add(current.ref);
        try{const result=await api('/api/query-open',{job_ref:current.ref,revision:current.original_revision,resolution_revision:current.original_resolution_revision});if(!stopped){applyReading(result);setJob(result.query_job);setEntryOpen(false);setMessage(result.resolution?.has_card?'Card acquired. Further browsing reads this capture without refreshing sources.':'Source query finished. Inspect its original outcome.');}}
        catch{if(!stopped)setMessage('Source result ready. Your reading changed; choose Open result when you want to inspect it.');}}
      else if(current.state==='failed'&&!stopped)setMessage(current.error??'Source query failed. Your previous reading remains available.');
    }catch(error){if(!stopped)setMessage(String(error));}finally{pending=false;}}
    const timer=setInterval(()=>void poll(),500);void poll();return()=>{stopped=true;clearInterval(timer);};
  },[job?.ref,queryWatch]);
  async function cancelQuery(){if(!job)return;try{const result=await api('/api/query-cancel',{job_ref:job.ref});setJob(result.query_job);setMessage(result.query_job.worker_running?'Result discarded. An active source request may finish; browsing remains available.':'Query result discarded.');}catch(error){setMessage(String(error));}}
  async function openQueryResult(){if(!job||busy)return;setBusy(true);try{const result=await api('/api/query-open',{job_ref:job.ref,revision:panel?.revision??'',resolution_revision:resolution?.revision??''});applyReading(result);setJob(result.query_job);setEntryOpen(false);setMessage('Opened the retained source result. No new source query was made.');}catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function workspaceAction(reopen=false){if(busy)return;setBusy(true);setMessage(reopen?'Reopening the original workspace…':'Saving the current readings and source-query history…');
    try{const result=await api(reopen?'/api/workspace-reopen':'/api/workspace-save',{revision:panel?.revision??'',resolution_revision:resolution?.revision??''});applyReading(result);
      setMessage(reopen?'Original workspace reopened. No sources queried; layout and molecular model are separate.':'Workspace saved: original readings, Card/Deck navigation and source-query history. Pending queries, layout and molecular scene are not included.');}
    catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function saveLayout(workspace:SerializedDockview){if(busy)return;setBusy(true);try{const result=await api('/api/layout',{format:'sabueso.presentation_layout@1',renderer:'dockview@8.9.0',workspace});setPresentation(result);setMessage('Presentation layout saved. This does not save Knowledge, query history or the molecular scene.');}catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function act(name:string,extra:Record<string,unknown>={}){if(!panel||busy)return;setBusy(true);setMessage('Opening the requested reading…');
    try{const result=await api('/api/action',{name,revision:panel.revision,...extra});setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution??null);setCanReturnQuery(result.can_return_query??false);setMessage(name==='save'?(panel.workspace==='deck'?'Deck reading saved: original members, metadata, selection and Back history. Layout, source queries and molecular scene are not included.':panel.deck_context!==undefined?'Card reading and captured Cards saved. Deck membership, selection and layout are not saved in this file.':'Reading saved. Reopen it to inspect the original capture.'):'Ready.');}
    catch(error){setMessage(String(error));try{const current=await api('/api/panel');setPanel(current.panel);setResolution(current.resolution??null);setCanReturnQuery(current.can_return_query??false);}catch{setMessage('The reading service is unavailable. Reopen the application to continue.');}}
    finally{setBusy(false);}}
  async function openFile(selected:File){setBusy(true);try{
    if(selected.size>16*1024**2)throw new Error('This input exceeds the 16 MiB opening limit.');
    const response=await fetch(`/api/${fileMode}`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Sabueso-Revision':panel?.revision??'','X-Sabueso-Resolution':resolution?.revision??''},body:selected});if(!response.ok){const error=await response.json();throw new Error(error.error??'Could not open the Card.');}const result=await response.json();applyReading(result);setMessage(`${fileMode==='deck'?'Deck':fileMode==='reading'?'Original reading':'Card'} opened. Choose where to explore.`);
    }catch(error){setMessage(String(error));}finally{setBusy(false);if(file.current)file.current.value='';}}
  async function acquire(choice_ref?:string){if(!ready||busy||queryActive)return;setBusy(true);setMessage('Starting the requested public-source query…');
    try{const revisions={revision:panel?.revision??'',resolution_revision:resolution?.revision??''};
      const result=await api(choice_ref?'/api/query-choice':'/api/query-start',choice_ref?{...revisions,choice_ref}:{...revisions,kind:entryKind,query:identifier,...(entryKind==='uniprot'?{protein_source:proteinSource}:{})});
      setJob(result.query_job);setEntryOpen(false);setMessage('Querying sources in the background. Your current reading remains available.');
    }catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function queryRecord(item_ref:string){if(!ready||busy||queryActive||!panel)return;setBusy(true);
    try{const result=await api('/api/query-link',{item_ref,revision:panel.revision,resolution_revision:resolution?.revision??''});setJob(result.query_job);setEntryOpen(false);setMessage('Querying the referenced source record as a new capture. This original reading remains available; no identity is merged.');}
    catch(error){setMessage(String(error));}finally{setBusy(false);}}
  async function returnQuery(){if(busy)return;setBusy(true);try{const result=await api('/api/resolve-back',{revision:panel?.revision??'',resolution_revision:resolution?.revision??''});setPanel(result.panel);setMolecular(result.molecular??null);setResolution(result.resolution);setCanReturnQuery(result.can_return_query);setMessage('Returned to the exact retained query and reading. No source was queried.');}catch(error){setMessage(String(error));}finally{setBusy(false);}}
  const entry=<form className="entry-form" aria-label="Query public sources" onSubmit={e=>{e.preventDefault();void acquire();}}>
    <label htmlFor="entry-kind">Start from</label><select id="entry-kind" value={entryKind} disabled={busy||queryActive} onChange={e=>setEntryKind(e.target.value)}><option value="uniprot">UniProt accession</option><option value="pdb">PDB entry</option><option value="smiles">SMILES</option><option value="disease">Disease identifier</option></select>
    <label htmlFor="entry-query">{entryKind==='smiles'?'Public molecular structure (SMILES)':'Identifier'}</label><input id="entry-query" maxLength={8192} value={identifier} disabled={busy||queryActive} onChange={e=>setIdentifier(e.target.value)} placeholder={{uniprot:'P52270',pdb:'1TCD',smiles:'CCO',disease:'MONDO:0014221'}[entryKind]}/>
    {entryKind==='uniprot'&&<><label htmlFor="protein-source">Query scope</label><select id="protein-source" value={proteinSource} disabled={busy||queryActive} onChange={e=>setProteinSource(e.target.value)}><option value="identity">Identity and UniProt annotations</option><option value="interpro">Also ask InterPro for source-mapped sites</option><option value="alphafold">Also ask AlphaFold DB for predicted-model records</option></select><p className="quiet">{proteinSource==='identity'?'No additional source requested.':proteinSource==='interpro'?'Queries UniProt and the InterPro site-residue endpoint for this protein. Positions are as stated by InterPro; no alignment or 3D correspondence is inferred.':'Queries UniProt and the AlphaFold prediction API for this protein. Model records are predictions; coordinates are not downloaded or displayed automatically.'} A new capture opens when ready; Return to previous query restores your original reading.</p></>}
    <button className="primary" disabled={!ready||busy||queryActive||!identifier.trim()}>Query public sources</button>
    <p className="quiet">{entryKind==='smiles'?'The entered SMILES is sent to PubChem for source-stated identity. UniChem expansion is disabled for this initial query.':entryKind==='disease'?'The disease identifier is sent to MONDO. Disease-name search is not offered yet.':entryKind==='pdb'?'The entry identifier is sent to RCSB PDB. Related proteins are offered for a separate query.':'The accession is sent to UniProt.'} Uses identity@1 with only the additional protein source explicitly selected above. Browsing never refreshes sources.</p>
  </form>;
  return <><header><div className="brand"><span className="brand-mark">S</span><div><h1>Sabueso</h1><p>Molecular knowledge explorer</p></div></div>
    {canReturnQuery&&<button disabled={busy} onClick={()=>void returnQuery()}>Return to previous query</button>}<button disabled={!ready||busy} aria-expanded={!!panel&&entryOpen} onClick={()=>setEntryOpen(!entryOpen)}>{panel&&entryOpen?'Hide source query':'New source query'}</button><button disabled={!ready||busy} onClick={()=>{setFileMode('card');file.current?.click();}}>Open Card…</button><button disabled={!ready||busy} onClick={()=>{setFileMode('deck');file.current?.click();}}>Open Deck…</button><button disabled={!ready||busy} onClick={()=>{setFileMode('reading');file.current?.click();}}>Open reading…</button><button disabled={!ready||busy||(!panel&&!resolution)} onClick={()=>void workspaceAction()}>Save workspace</button>{workspaceSaved&&<button disabled={busy} onClick={()=>void workspaceAction(true)}>Reopen workspace</button>}<input ref={file} type="file" accept={fileMode==='deck'?'.jsonl':fileMode==='reading'?'.json,.gz,.zst,application/json':'.json,application/json'} hidden onChange={e=>{const f=e.target.files?.[0];if(f)void openFile(f);}}/></header>
    <div role="status" className={message.startsWith('Error')?'status error':'status'} aria-live="polite">{message}</div>
    {job&&job.state!=='opened'&&<section className="query-progress" aria-label="Source query progress"><div><strong>{job.state==='running'?'Querying public sources':job.state==='ready'?'Source result ready':job.state==='cancelled'?'Result discarded':'Source query failed'}</strong><span>{job.query}{job.protein_source&&job.protein_source!=='identity'?` · additional source: ${job.protein_source}`:''}</span><span>{job.worker_running?'A provider request is still running. Your current reading remains available.':job.state==='ready'?'Ready to open the retained answer.':job.error??'No pending result will replace your reading.'}</span></div>
      {(job.state==='running'||job.state==='ready')&&<button onClick={()=>void cancelQuery()}>Cancel query</button>}{job.state==='ready'&&<button disabled={busy} onClick={()=>void openQueryResult()}>Open result</button>}</section>}
    {entryOpen&&panel&&<section className="query-drawer">{entry}</section>}{resolution&&<ResolutionReport result={resolution} busy={busy||queryActive} choose={ref=>acquire(ref)}/>}
    {!panel?<main className="welcome"><div className="eyebrow">Start an exploration</div><h2>What would you like to learn?</h2>
      <p>Choose an identifier to query public sources, or open a local Card or Deck to explore retained knowledge.</p>{entry}
      <button className="primary" disabled={!ready||busy} onClick={()=>{setFileMode('card');file.current?.click();}}>Open a Card JSON file</button><p className="quiet">Opening files and browsing topics makes no source queries. No account required.</p></main>:
    <main className="application"><aside><div className="eyebrow">{panel.profile.replaceAll('_',' ')} knowledge</div><h2>{panel.workspace==='deck'?'Choose a member':'Choose a topic'}</h2>
      <form onSubmit={e=>{e.preventDefault();void act('search',{text:query});}}><label htmlFor="search">{panel.workspace==='deck'?'Filter member identifiers or natures':'Search retained content'}</label><div className="search"><input id="search" maxLength={512} value={query} onChange={e=>setQuery(e.target.value)} placeholder="A name, annotation, or term"/><button disabled={busy||!query.trim()}>Search</button></div></form>
      <nav className="topics" aria-label="Card topics">{panel.workspace==='deck'&&<><button onClick={()=>void act('metadata')} disabled={busy}>Original membership and metadata</button><button onClick={()=>void act('sort',{column:'label',descending:false})} disabled={busy}>Order by identifier</button><button onClick={()=>void act('sort',{column:'kind',descending:false})} disabled={busy}>Order by nature</button><button onClick={()=>void act('sort',{column:'label',descending:true})} disabled={busy}>Reverse identifier order</button></>}{panel.topics.map(topic=><button key={topic.name} disabled={busy} onClick={()=>void act('topic',{topic:topic.name})} data-topic={topic.name}>
        <strong>{topic.name.replaceAll('_',' ')}</strong><span>{topic.description}</span>{topic.availability==='not_saved'&&<em>Not saved in this original reading</em>}</button>)}</nav></aside>
      <section className="main-reading" aria-label="Knowledge workspace"><nav className="actions" aria-label="Reading navigation"><button disabled={busy||!panel.can_back} onClick={()=>void act('back')}>Back</button><button disabled={busy} onClick={()=>void act('overview')}>Overview</button><span/>{panel.deck_context!==undefined&&<button disabled={busy} onClick={()=>void act('deck')}>Return to Deck</button>}
        <button disabled={busy||!panel.can_save} onClick={()=>void act('save')}>{panel.workspace==='deck'?'Save Deck reading':'Save reading'}</button><button disabled={busy||!panel.saved_file} onClick={()=>void act('reopen')}>Reopen saved</button></nav>
        <Workspace panel={panel} busy={busy} act={act} queryBusy={queryActive} queryRecord={queryRecord} molecular={molecular} presentation={presentation} saveLayout={saveLayout} notice={setMessage}/></section></main>}</>;
}
createRoot(document.getElementById('root')!).render(<App/>);
