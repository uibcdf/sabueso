// Only the provider's exported experimental molecular surface is used here.
import * as api from '/sketcher/index.js';
const corpus=(await(await fetch('/corpus.json')).json()).cases;
const events=[],hovers=[];
const a=api.createMolecularSvgView(document.querySelector('#a'),{instanceId:'sabueso-qt-a'});
const b=api.createMolecularSvgView(document.querySelector('#b'),{instanceId:'sabueso-qt-b',theme:'dark'});
a.subscribeSelection(pick=>events.push(pick));a.subscribeHover(pick=>hovers.push(pick));
await Promise.all([a.ready,b.ready]);
const accepted=await Promise.all([a.replace(corpus[0].document),b.replace(corpus[0].document)]);
if(accepted.some(result=>result.status!=='accepted'))throw new Error('The initial provider controls were not accepted');
function describe(){
  const h=window.sketcherReceiving;
  document.querySelector('#source').textContent=['a','b'].map(name=>{
    const input=h[name].state.accepted?.document;
    return name.toUpperCase()+': '+(input?input.id+' · original '+JSON.stringify(input.original.source):'No accepted drawing');
  }).join('\n')+'\nDrawing coordinates are nonphysical; no Card or active 3D mapping is established.';
}
window.sketcherReceiving={api,corpus,a,b,events,hovers,describe};describe();
