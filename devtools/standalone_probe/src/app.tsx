import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { DockviewReact, type DockviewApi, type DockviewReadyEvent } from 'dockview-react';
import 'dockview-react/dist/styles/dockview.css';
import './style.css';

type Panel = {
  title: string;
  text: string;
  result_ref: string;
  view_ref: string;
  items: {ref: string; label: string}[];
  can_back: boolean;
  mode: string;
  reopen_validation: null | Record<string, boolean>;
  is_source_assertion: boolean;
};
type Config = {viewer_url: string; card_ref: string; topics: string[]; panel: Panel; scope: string};
type MolecularState = {
  binding_valid: boolean;
  viewer_ready: boolean;
  structure_complete: boolean;
  client_registrations: number;
  active_selection: number[];
  pick: null | {atom_indices: number[]; source_locations: {source_asym_id: string; uniprot_position: number | null}[]};
};
type Action = {name: string; topic?: string; item_ref?: string};
type Session = {config: Config; independentUrl: string | null; panel: Panel; molecular: MolecularState | null; act: (action: Action) => Promise<void>};
const SessionContext = createContext<Session | null>(null);
const useSession = () => useContext(SessionContext)!;
const metrics = {iframe_loads: 0, molecule_mounts: 0, molecule_unmounts: 0, ui_ready_ms: 0, actions_completed: 0};
declare global {
  interface Window {
    __sabuesoProbe: {metrics: typeof metrics; api: DockviewApi | null; getState: () => unknown};
  }
}
window.__sabuesoProbe = {metrics, api: null, getState: () => null};

async function jsonRequest(path: string, body?: unknown) {
  const response = await fetch(path, {
    credentials: 'same-origin',
    cache: 'no-store',
    ...(body === undefined ? {} : {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
    }),
  });
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  return response.json();
}

function MolecularPanel() {
  const {config} = useSession();
  useEffect(() => {
    metrics.molecule_mounts++;
    return () => { metrics.molecule_unmounts++; };
  }, []);
  return <iframe title="Live molecular representation of public 1TCD" data-testid="molecular-frame"
    src={config.viewer_url} onLoad={() => {metrics.iframe_loads++;}} />;
}

function ReadingPanel() {
  const {panel, act} = useSession();
  return <article className="reading" data-testid="reading" data-result-ref={panel.result_ref} data-mode={panel.mode}>
    <h2>{panel.title}</h2>
    <p className="scope">Original captured knowledge · {panel.mode}</p>
    <pre data-testid="reading-text">{panel.text}</pre>
    <div className="items">
      {panel.items.map(item => <div className="item" key={item.ref}>
        <span>{item.label}</span>
        <button onClick={() => void act({name: 'open', item_ref: item.ref})}>Open</button>
        <button onClick={() => void act({name: 'related', item_ref: item.ref})}>Sources / questions</button>
      </div>)}
    </div>
  </article>;
}

function IndependentPanel() {
  const {independentUrl} = useSession();
  return independentUrl ? <iframe title="Independent live view of the same public input" src={independentUrl} data-testid="independent-frame"/> : null;
}

function ContextPanel() {
  const {molecular} = useSession();
  const picked = molecular?.pick;
  return <article className="reading">
    <h2>Molecular context</h2>
    <p>The original 1TCD coordinate file is linked to the TcTIM Card through the retained source alignment.</p>
    <p>Active selection: {molecular?.active_selection.length ?? 0} atoms.</p>
    {picked ? <p data-testid="picked-context">Picked {picked.atom_indices.length} atoms: {
      [...new Set(picked.source_locations.map(row => `chain ${row.source_asym_id}, UniProt position ${row.uniprot_position ?? 'not assigned'}`))].join('; ')
    }</p> : <p>Select the annotated site or click the molecular representation.</p>}
    <p>Water and other coordinate-only records retain their own identities.</p>
  </article>;
}

function HiddenContextPanel() {
  return <article className="reading"><h2>Other context</h2><p>The molecular tab is retained while this tab is visible.</p></article>;
}

// Stable component identities matter: updating a reading must not remount the molecular iframe.
const components = {molecule: MolecularPanel, reading: ReadingPanel, context: ContextPanel, hidden: HiddenContextPanel, independent: IndependentPanel};

function App({config}: {config: Config}) {
  const [panel, setPanel] = useState(config.panel);
  const [molecular, setMolecular] = useState<MolecularState | null>(null);
  const [independentUrl, setIndependentUrl] = useState<string | null>(null);
  const [message, setMessage] = useState('Opening the live molecular representation…');
  const [busy, setBusy] = useState(false);
  const api = useRef<DockviewApi | null>(null);

  async function act(action: Action) {
    setBusy(true);
    try {
      if (action.name === 'close_independent') api.current?.getPanel('independent')?.api.close();
      const value = await jsonRequest('/api/action', action);
      setPanel(value.panel);
      setIndependentUrl(value.independent_url);
      if (action.name === 'open_independent') api.current?.addPanel({id:'independent',component:'independent',title:'Independent 1TCD view',renderer:'always',
        position:{referencePanel:'molecule',direction:'below'},initialHeight:280});
      setMessage(`Completed: ${action.name.replaceAll('_', ' ')}`);
    } catch (error) {
      setMessage(String(error));
    } finally {setBusy(false); window.setTimeout(() => {metrics.actions_completed++;}, 0);}
  }

  useEffect(() => {
    let stopped = false;
    let pending = false;
    async function poll() {
      if (stopped || pending || document.visibilityState === 'hidden') return;
      pending = true;
      try {
        const state = await jsonRequest('/api/state');
        if (!stopped) setMolecular(state);
      } catch (error) {
        if (!stopped) setMessage(String(error));
      } finally {pending = false;}
    }
    void poll();
    const timer = window.setInterval(() => void poll(), 500);
    return () => {stopped = true; clearInterval(timer);};
  }, []);

  useEffect(() => {
    window.__sabuesoProbe.getState = () => ({panel, molecular, busy, message});
  }, [panel, molecular, busy, message]);

  function onReady(event: DockviewReadyEvent) {
    api.current = event.api;
    window.__sabuesoProbe.api = event.api;
    event.api.addPanel({id: 'molecule', component: 'molecule', title: '1TCD · live molecular view', renderer: 'always'});
    event.api.addPanel({id: 'reading', component: 'reading', title: 'Knowledge', renderer: 'always',
      position: {referencePanel: 'molecule', direction: 'right'}, initialWidth: 430});
    event.api.addPanel({id: 'context', component: 'context', title: 'Selection context',
      position: {referencePanel: 'reading', direction: 'below'}, initialHeight: 210});
    metrics.ui_ready_ms = performance.now();
    document.documentElement.dataset.probeReady = 'true';
  }

  function floatReading() {
    const reading = api.current?.getPanel('reading');
    if (reading) api.current?.addFloatingGroup(reading, {width: 430, height: 390, x: 60, y: 60});
  }
  function dockReading() {
    const molecule = api.current?.getPanel('molecule');
    if (molecule) api.current?.getPanel('reading')?.api.moveTo({group: molecule.api.group, position: 'right'});
  }
  function hideMolecule() {
    const current = api.current;
    if (!current || !current.getPanel('molecule')) return;
    const cover = current.getPanel('hidden') ?? current.addPanel({id: 'hidden', component: 'hidden', title: 'Other context',
      position: {referencePanel: 'molecule', direction: 'within'}});
    cover.api.setActive();
  }
  function showMolecule() {api.current?.getPanel('molecule')?.api.setActive();}
  function floatMolecule() {
    const molecule = api.current?.getPanel('molecule');
    if (molecule) api.current?.addFloatingGroup(molecule, {width: 560, height: 450, x: 30, y: 30});
  }
  function dockMolecule() {
    const context = api.current?.getPanel('context');
    if (context) api.current?.getPanel('molecule')?.api.moveTo({group: context.api.group, position: 'left'});
  }
  const session = {config, independentUrl, panel, molecular, act};
  return <SessionContext.Provider value={session}>
    <header><div><strong>Sabueso</strong><span className="subtitle">Molecular knowledge exploration</span></div>
      <span className="scope">Development comparison · public offline inputs</span></header>
    <div className="entity"><h1>TcTIM <small>UniProt P52270 · PDB 1TCD</small></h1>
      <span>{molecular && !molecular.binding_valid ? 'Model changed — source rebinding required' : molecular?.structure_complete ? 'Live structure received' : 'Waiting for structure'}</span></div>
    <div className="toolbar" aria-label="Exploration and layout controls">
      <button disabled={busy || !panel.can_back} onClick={() => void act({name: 'back'})}>Back</button>
      <button disabled={busy || !molecular?.structure_complete || !molecular?.binding_valid} onClick={() => void act({name: 'select_active_site'})}>Select annotated site</button>
      <button disabled={busy} onClick={() => void act({name: 'save'})}>Save reading</button>
      <button disabled={busy} onClick={() => void act({name: 'reopen'})}>Reopen reading</button>
      <button onClick={floatReading}>Float reading</button><button onClick={dockReading}>Dock reading</button>
      <button onClick={hideMolecule}>Hide molecule</button><button onClick={showMolecule}>Show molecule</button>
      <button onClick={floatMolecule}>Float molecule</button><button onClick={dockMolecule}>Dock molecule</button>
      <button disabled={busy || !!independentUrl} onClick={() => void act({name:'open_independent'})}>Open independent view</button>
      <button disabled={busy || !independentUrl} onClick={() => void act({name:'close_independent'})}>Close independent view</button>
    </div>
    <main>
      <nav aria-label="Available Card topics"><h2>Explore this Card</h2>
        <p>Choose what to read.</p>
        {config.topics.map(topic => <button key={topic} data-topic={topic} disabled={busy}
          onClick={() => void act({name: 'topic', topic})}>{topic.replaceAll('_', ' ')}</button>)}
      </nav>
      <section className="workspace" aria-label="Composable knowledge and molecular views">
        <DockviewReact className="dockview-theme-light" components={components} onReady={onReady}/>
      </section>
    </main>
    <footer role="status" data-testid="status" data-busy={busy}>{message}</footer>
  </SessionContext.Provider>;
}

async function start() {
  const token = new URLSearchParams(location.hash.slice(1)).get('token');
  if (token) {
    await jsonRequest('/auth', {token});
    history.replaceState(null, '', location.pathname);
  }
  const config = await jsonRequest('/api/config') as Config;
  createRoot(document.getElementById('root')!).render(<App config={config}/>);
}
void start().catch(error => {document.getElementById('root')!.textContent = String(error);});
