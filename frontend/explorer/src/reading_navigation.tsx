type Point={index:number;title:string};

function compact(text:string,limit:number){
  const characters=Array.from(text);
  if(characters.length<=limit)return text;
  const prefix=Math.ceil((limit-3)*.6),suffix=limit-3-prefix;
  return characters.slice(0,prefix).join('')+' … '+characters.slice(-suffix).join('');
}

export function ReadingHeading({title}:{title:string}){
  const label=compact(title,48);
  return <div className="reading-heading"><h2 className="reading-title" title={title} tabIndex={-1} data-reading-control="heading">{label}</h2>
    {label!==title&&<details className="reading-title-disclosure"><summary data-reading-control="full_title">Full reading title</summary><p>{title}</p></details>}
  </div>;
}

export function ReadingTrail({points,busy,select}:{points:Point[];busy:boolean;select:(index:number)=>void}){
  if(!points.length)return null;
  const earlier=points.slice(0,-5),recent=points.slice(-5);
  function pointButton(point:Point,full=false){return <button key={point.index} data-reading-control="trail" data-history-index={point.index} disabled={busy} title={point.title} aria-label={point.title} onClick={()=>select(point.index)}>{full?point.title:compact(point.title,48)}</button>;}
  return <nav className="reading-trail" aria-label="Reading trail">
    {!!earlier.length&&<details className="earlier-trail"><summary>Earlier readings ({earlier.length})</summary><div>{earlier.map(point=>pointButton(point,true))}</div></details>}
    {recent.map(point=>pointButton(point))}
  </nav>;
}
