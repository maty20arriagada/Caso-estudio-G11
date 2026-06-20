"""
05_dashboard_build.py
=================================================================
Genera el dashboard HTML autocontenido (ECharts incrustado offline)
a partir de output/dashboard_data.json.
Salida: output/dashboard.html  (se abre directo en el navegador)
=================================================================
"""
from pathlib import Path
import cmpc_utils as U

DATA_JSON = (U.OUT / "dashboard_data.json").read_text(encoding="utf-8")
ECHARTS = (U.BASE / "parte1" / "vendor" / "echarts.min.js").read_text(encoding="utf-8")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Productividad - Aserradero CMPC Mulchen (Parte 1)</title>
<script>__ECHARTS__</script>
<style>
:root{
  --bg:#eef1f5; --card:#ffffff; --head:#16243b; --head2:#22344f;
  --ink:#1d2733; --muted:#64748b; --line:#e3e8ef;
  --accent:#1565c0; --good:#2e7d32; --warn:#ef6c00; --bad:#c62828;
  --gap:16px; --radius:12px;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.5;font-size:14px}
.wrap{max-width:1500px;margin:0 auto;padding:var(--gap)}
header.top{background:linear-gradient(135deg,var(--head),var(--head2));color:#fff;
  padding:22px 26px;border-radius:var(--radius);margin-bottom:var(--gap);
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;
  box-shadow:0 4px 14px rgba(0,0,0,.12)}
header.top h1{font-size:21px;font-weight:700;letter-spacing:.2px}
header.top .sub{font-size:12.5px;color:#aebfd6;margin-top:3px}
.ctrl{display:flex;gap:10px;align-items:center}
.ctrl label{font-size:12px;color:#aebfd6}
.ctrl select{padding:8px 12px;border-radius:8px;border:1px solid #33445f;
  background:#0f1a2c;color:#fff;font-size:13px;font-weight:600;cursor:pointer}
.note{background:#fff;border-left:4px solid var(--accent);border-radius:8px;
  padding:12px 16px;margin-bottom:var(--gap);font-size:12.8px;color:#475569;
  box-shadow:0 1px 3px rgba(0,0,0,.05)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.kpi{background:var(--card);border-radius:var(--radius);padding:16px 18px;
  box-shadow:0 1px 4px rgba(0,0,0,.07);border-top:3px solid var(--accent);position:relative}
.kpi .lbl{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:600}
.kpi .val{font-size:25px;font-weight:800;margin-top:5px;line-height:1.1}
.kpi .ci{font-size:11.5px;color:var(--muted);margin-top:3px}
.kpi.red{border-top-color:var(--bad)} .kpi.green{border-top-color:var(--good)}
.kpi.amber{border-top-color:var(--warn)}
.section{margin-bottom:var(--gap)}
.section h2{font-size:15px;font-weight:700;margin:6px 2px 10px;color:#0f1a2c;
  display:flex;align-items:center;gap:8px}
.section h2 .tag{font-size:10.5px;font-weight:700;background:#e3edfb;color:var(--accent);
  padding:2px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px}
.desc{font-size:12.3px;color:var(--muted);margin:0 2px 10px}
.grid{display:grid;gap:var(--gap)}
.g2{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.card{background:var(--card);border-radius:var(--radius);padding:16px 18px;
  box-shadow:0 1px 4px rgba(0,0,0,.07)}
.card h3{font-size:13px;font-weight:700;margin-bottom:4px;color:#27364b}
.card .h3sub{font-size:11.5px;color:var(--muted);margin-bottom:8px}
.chart{width:100%;height:320px}
.chart-lg{width:100%;height:420px}
.chart-flow{width:100%;height:500px}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:11.5px;color:#475569;margin-top:8px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
table.dt{width:100%;border-collapse:collapse;font-size:12.5px}
table.dt th,table.dt td{padding:9px 11px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
table.dt th:first-child,table.dt td:first-child{text-align:left}
table.dt thead th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.4px;
  cursor:pointer;user-select:none;border-bottom:2px solid #cfd8e3}
table.dt tbody tr:hover{background:#f6f9fd}
table.dt .bn{font-weight:800;color:var(--bad)}
.footer{color:var(--muted);font-size:11.5px;text-align:center;padding:14px}
.pill{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:20px}
.pill.t247{background:#e8f0fe;color:#1a56c4} .pill.tturno{background:#fff1e6;color:#b85c00}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div>
    <h1>Dashboard de Productividad &mdash; Aserradero CMPC Mulch&eacute;n</h1>
    <div class="sub">Caso de Estudio &middot; Parte 1: disponibilidad, cuello de botella y flujo de material &middot; Dise&ntilde;o de Sistemas de Producci&oacute;n</div>
  </div>
  <div class="ctrl">
    <label>Vista de datos</label>
    <select id="repsel"></select>
  </div>
</header>

<div class="note" id="methnote"></div>

<div class="kpis" id="kpis"></div>

<!-- FLUJO DE MATERIAL -->
<div class="section">
  <h2><span class="tag">Flujo</span> Flujo de material (Sankey)</h2>
  <div class="desc">Balance de materia anual (m&sup3;/a&ntilde;o): de los trozos a los productos terminados, con las mermas de cada etapa. El ancho de cada banda es proporcional al volumen.</div>
  <div class="card"><div id="sankey" class="chart-flow"></div></div>
</div>

<!-- DIAGRAMA DE LINEA -->
<div class="section">
  <h2><span class="tag">Flujo</span> Diagrama de la l&iacute;nea (estados, buffers y WIP)</h2>
  <div class="desc">Topolog&iacute;a del proceso. Las estaciones se colorean por <b>utilizaci&oacute;n</b> (verde&rarr;rojo) y los buffers por su <b>nivel de WIP</b>. El grosor de las flechas es el flujo de material. Pasa el cursor para ver el detalle de cada nodo. Se puede arrastrar y hacer zoom.</div>
  <div class="card"><div id="graph" class="chart-flow"></div>
    <div class="legend">
      <span><i style="background:#2e7d32"></i>baja utilizaci&oacute;n</span>
      <span><i style="background:#fbc02d"></i>media</span>
      <span><i style="background:#c62828"></i>alta (cuello de botella)</span>
      <span><i style="background:#90a4ae"></i>buffer</span>
      <span><i style="background:#6d4c41"></i>trozos</span>
      <span><i style="background:#4C72B0"></i>producto terminado</span>
      <span><i style="background:#cfd8dc"></i>mermas</span>
    </div>
  </div>
</div>

<!-- DISPONIBILIDAD -->
<div class="section">
  <h2><span class="tag">Disponibilidad</span> Disponibilidad, utilizaci&oacute;n y confiabilidad</h2>
  <div class="desc">Indicadores del cuello de botella (gauges) y comparaci&oacute;n entre estaciones. Disponibilidad = MTBF/(MTBF+MTTR); Utilizaci&oacute;n = BUSY / tiempo programado; OEE &asymp; Disponibilidad &times; eficiencia de setup &times; yield.</div>
  <div class="grid g2">
    <div class="card"><h3>Gauges del cuello de botella (Aserradero)</h3><div class="h3sub">la m&aacute;quina cr&iacute;tica del sistema</div><div id="gauges" class="chart"></div></div>
    <div class="card"><h3>Utilizaci&oacute;n vs Disponibilidad por estaci&oacute;n</h3><div class="h3sub">barras con IC95% en el modo Promedio</div><div id="utildisp" class="chart"></div></div>
  </div>
  <div class="card" style="margin-top:var(--gap)"><h3>Composici&oacute;n del tiempo por estado</h3><div class="h3sub">% del tiempo total &middot; revela inanici&oacute;n (IDLE), setup, fallas (DOWN) y fuera de turno</div><div id="statecomp" class="chart"></div>
    <div class="legend" id="statelegend"></div>
  </div>
</div>

<!-- CUELLO DE BOTELLA -->
<div class="section">
  <h2><span class="tag">Restricci&oacute;n</span> An&aacute;lisis de cuello de botella</h2>
  <div class="desc">El cuello de botella es el recurso de mayor utilizaci&oacute;n; aguas arriba se acumula WIP y aguas abajo las estaciones se hambrean. El crecimiento sostenido del patio de trozos (log_yard) confirma la saturaci&oacute;n.</div>
  <div class="grid g2">
    <div class="card"><h3>Ranking de utilizaci&oacute;n</h3><div class="h3sub">identifica la restricci&oacute;n</div><div id="utilrank" class="chart"></div></div>
    <div class="card"><h3>WIP por buffer en el tiempo</h3><div class="h3sub">log_yard crece sin acotarse (eje izq.); buffers intermedios estables (eje der.)</div><div id="wiptime" class="chart"></div></div>
  </div>
  <div class="card" style="margin-top:var(--gap)"><h3>Arribos de trozos vs capacidad de procesamiento</h3><div class="h3sub">m&sup3;/d&iacute;a &middot; el exceso de arribos alimenta el backlog del patio</div><div id="arrproc" class="chart"></div></div>
</div>

<!-- FALLAS -->
<div class="section">
  <h2><span class="tag">Confiabilidad</span> An&aacute;lisis de fallas</h2>
  <div class="desc">Validaci&oacute;n del enunciado: las fallas ocurren durante el procesamiento. Las "fallas fuera de horario" se explican por estaciones 24/7 y por overrun de lote (la regla solo proh&iacute;be <i>iniciar</i> lotes fuera de turno, no <i>terminarlos</i>).</div>
  <div class="grid g3">
    <div class="card"><h3>Fallas por estaci&oacute;n</h3><div class="h3sub">por a&ntilde;o</div><div id="failstation" class="chart"></div></div>
    <div class="card"><h3>Clasificaci&oacute;n de fallas</h3><div class="h3sub">dentro/fuera de la ventana operativa</div><div id="failclass" class="chart"></div></div>
    <div class="card"><h3>Distribuci&oacute;n horaria</h3><div class="h3sub">turno vs 24/7 &middot; franja 07&ndash;23 sombreada</div><div id="failhour" class="chart"></div></div>
  </div>
</div>

<!-- PRODUCCION -->
<div class="section">
  <h2><span class="tag">Producci&oacute;n</span> Producci&oacute;n y tiempos de ciclo</h2>
  <div class="grid g3">
    <div class="card"><h3>Producci&oacute;n por producto</h3><div class="h3sub">m&sup3;/a&ntilde;o</div><div id="prodprod" class="chart"></div></div>
    <div class="card"><h3>Throughput diario</h3><div class="h3sub">volumen terminado &middot; warm-up sombreado</div><div id="throughtime" class="chart"></div></div>
    <div class="card"><h3>Lead time por producto</h3><div class="h3sub">horas &middot; caja=Q1-Q3, bigotes=P5-P95</div><div id="leadbox" class="chart"></div></div>
  </div>
</div>

<!-- TABLA -->
<div class="section">
  <h2><span class="tag">Detalle</span> Tabla de KPIs por estaci&oacute;n</h2>
  <div class="card" style="overflow-x:auto"><div id="tablewrap"></div></div>
</div>

<div class="footer" id="foot"></div>
</div>

<script>
const DATA = __DATA__;
const META = DATA.meta;
const SC = META.state_colors, PC = META.product_colors;
const STATIONS = META.stations, STATES = META.states, BUFFERS = META.buffers;
let V = DATA.views['avg'];
let CHARTS = {};

// ---------- helpers ----------
const fmt = (x,d=0)=> x==null?'-':x.toLocaleString('es-CL',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct = (x,d=1)=> x==null?'-':(x*100).toFixed(d)+'%';
const hrs = (x,d=1)=> x==null?'-':x.toFixed(d)+' h';
function utilColor(u){ // verde -> amarillo -> rojo
  u=Math.max(0,Math.min(1,u));
  const stops=[[0.0,[46,125,50]],[0.5,[251,192,45]],[1.0,[198,40,40]]];
  let a=stops[0],b=stops[2];
  for(let i=0;i<stops.length-1;i++){ if(u>=stops[i][0]&&u<=stops[i+1][0]){a=stops[i];b=stops[i+1];break;} }
  const t=(u-a[0])/((b[0]-a[0])||1);
  const c=a[1].map((v,i)=>Math.round(v+(b[1][i]-v)*t));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
function st(name){ return V.stations.find(s=>s.station===name); }
function initChart(id){ if(!CHARTS[id]) CHARTS[id]=echarts.init(document.getElementById(id)); return CHARTS[id]; }

// ---------- KPIs ----------
function renderKPIs(){
  const k=V.kpis, avg = (curKey==='avg');
  const cards=[
    {lbl:'Producci&oacute;n &uacute;til',val:fmt(k.prod_total)+' m&sup3;/a&ntilde;o',ci:avg&&k.prod_total_ci?('&plusmn; '+fmt(k.prod_total_ci)):'',cls:'green'},
    {lbl:'Throughput l&iacute;nea',val:fmt(k.throughput_dia,1)+' m&sup3;/d&iacute;a',ci:'salida del sistema',cls:''},
    {lbl:'Utilizaci&oacute;n cuello (Aserradero)',val:pct(k.util_bottleneck),ci:avg&&k.util_bottleneck_ci?('&plusmn; '+pct(k.util_bottleneck_ci)):'',cls:'red'},
    {lbl:'Disponibilidad Aserradero',val:pct(k.disp_bottleneck),ci:avg&&k.disp_bottleneck_ci?('&plusmn; '+pct(k.disp_bottleneck_ci)):'',cls:'amber'},
    {lbl:'OEE Aserradero',val:pct(k.oee_bottleneck),ci:'disp &times; setup &times; yield',cls:'amber'},
    {lbl:'Fallas',val:fmt(k.fallas_total)+'/a&ntilde;o',ci:'',cls:'red'},
    {lbl:'Backlog patio (log_yard)',val:'+'+fmt(k.logyard_slope,1)+' m&sup3;/d&iacute;a',ci:'acumula '+fmt(k.logyard_final)+' m&sup3;',cls:'red'},
    {lbl:'Lead time P3 (mediana)',val:hrs(k.leadtime_p3),ci:'desde aserradero',cls:''},
  ];
  document.getElementById('kpis').innerHTML = cards.map(c=>
    `<div class="kpi ${c.cls}"><div class="lbl">${c.lbl}</div><div class="val">${c.val}</div><div class="ci">${c.ci||''}</div></div>`).join('');
}

// ---------- Sankey ----------
function renderSankey(){
  const ch=initChart('sankey');
  const nodeColor={trozos:'#6d4c41',aserradero:'#c62828',bano:'#1565c0',secado:'#1565c0',
    drymill:'#1565c0',impregnado:'#1565c0',Mermas:'#b0bec5',P1:PC.P1,P2:PC.P2,P3:PC.P3};
  const names=['trozos','aserradero','bano','secado','drymill','impregnado','Mermas','P1','P2','P3'];
  const nodes=names.map(n=>({name:n,itemStyle:{color:nodeColor[n]||'#888'}}));
  const links=META.sankey_links.map(key=>{
    const [s,t]=key.split('>'); return {source:s,target:t,value:V.sankey[key]||0};
  });
  ch.setOption({
    tooltip:{trigger:'item',triggerOn:'mousemove',
      formatter:p=> p.dataType==='edge'?`${p.data.source} &rarr; ${p.data.target}<br><b>${fmt(p.data.value)}</b> m&sup3;/a&ntilde;o`:`<b>${p.name}</b>`},
    series:[{type:'sankey',left:'4%',right:'9%',top:'3%',bottom:'3%',
      nodeWidth:16,nodeGap:14,emphasis:{focus:'adjacency'},
      lineStyle:{color:'gradient',opacity:.45,curveness:.5},
      label:{fontSize:12,fontWeight:600,color:'#27364b'},
      data:nodes,links:links}]
  },true);
}

// ---------- Diagrama de linea (graph) ----------
function renderGraph(){
  const ch=initChart('graph');
  const P={trozos:[0,0],log_yard:[120,0],aserradero:[245,0],stock_aserrado:[365,0],
    bano:[485,-95],P1:[610,-95],secado:[485,95],stock_seco:[605,95],drymill:[725,95],
    P2:[850,25],stock_drymill:[725,205],impregnado:[850,205],P3:[975,205],Mermas:[250,-180]};
  const nodes=[]; const wipFinal={}; BUFFERS.forEach(b=>wipFinal[b]=V.series.wip[b][V.series.wip[b].length-1]);
  const maxWip=Math.max(...BUFFERS.map(b=>wipFinal[b]),1);
  function stTip(s){ return `<b>${s.station}</b> (${s.tipo})<br>Utilizaci&oacute;n: <b>${pct(s.util)}</b><br>Disponibilidad: ${pct(s.disp)}<br>`+
     `MTBF: ${fmt(s.mtbf)} h &middot; MTTR: ${fmt(s.mttr,1)} h<br>Yield: ${pct(s['yield'])} &middot; OEE: ${pct(s.oee)}<br>`+
     `<span style="color:#888">BUSY ${fmt(s.BUSY,0)}% &middot; IDLE ${fmt(s.IDLE,0)}% &middot; SETUP ${fmt(s.SETUP,0)}% &middot; DOWN ${fmt(s.DOWN,0)}% &middot; OFF ${fmt(s.OFF_SHIFT,0)}%</span>`; }
  STATIONS.forEach(name=>{ const s=st(name);
    nodes.push({name,x:P[name][0],y:P[name][1],symbol:'roundRect',symbolSize:[78,46],
      itemStyle:{color:utilColor(s.util),borderColor:'#fff',borderWidth:2},
      label:{show:true,formatter:`{b}\n${pct(s.util,0)}`,color:'#fff',fontWeight:700,fontSize:11,lineHeight:14},
      tooltip:{formatter:stTip(s)}}); });
  BUFFERS.forEach(b=>{ const lvl=wipFinal[b]; const heat=Math.min(1,lvl/maxWip);
    nodes.push({name:b,x:P[b][0],y:P[b][1],symbol:'rect',symbolSize:[58,30],
      itemStyle:{color:`rgb(${Math.round(144+ (198-144)*heat)},${Math.round(164-(164-40)*heat)},${Math.round(174-(174-40)*heat)})`,borderColor:'#607d8b',borderWidth:1},
      label:{show:true,formatter:`${b.replace('stock_','').replace('log_yard','patio')}\n${fmt(lvl)} m&sup3;`,color:'#fff',fontSize:9.5,fontWeight:600,lineHeight:12},
      tooltip:{formatter:`<b>${b}</b><br>WIP fin de horizonte: <b>${fmt(lvl)}</b> m&sup3;`}}); });
  [['trozos',[0,0],'#6d4c41'],['P1',P.P1,PC.P1],['P2',P.P2,PC.P2],['P3',P.P3,PC.P3],['Mermas',P.Mermas,'#cfd8dc']].forEach(([n,xy,c])=>{
    nodes.push({name:n,x:P[n][0],y:P[n][1],symbol:'circle',symbolSize:34,
      itemStyle:{color:c,borderColor:'#fff',borderWidth:2},
      label:{show:true,formatter:n==='trozos'?'Trozos':n,color:n==='Mermas'?'#546e7a':'#fff',fontSize:10,fontWeight:700},
      tooltip:{show:n!=='trozos'&&n!=='Mermas'}}); });
  const sl=V.sankey, maxV=Math.max(...Object.values(sl),1);
  const w=v=>1+11*(v/maxV);
  const E=[['trozos','log_yard',sl['trozos>aserradero']],['log_yard','aserradero',sl['trozos>aserradero']],
    ['aserradero','stock_aserrado',sl['aserradero>bano']+sl['aserradero>secado']],
    ['stock_aserrado','bano',sl['aserradero>bano']],['stock_aserrado','secado',sl['aserradero>secado']],
    ['bano','P1',sl['bano>P1']],['secado','stock_seco',sl['secado>drymill']],['stock_seco','drymill',sl['secado>drymill']],
    ['drymill','P2',sl['drymill>P2']],['drymill','stock_drymill',sl['drymill>impregnado']],
    ['stock_drymill','impregnado',sl['drymill>impregnado']],['impregnado','P3',sl['impregnado>P3']],
    ['aserradero','Mermas',sl['aserradero>Mermas']],['bano','Mermas',sl['bano>Mermas']],
    ['secado','Mermas',sl['secado>Mermas']],['drymill','Mermas',sl['drymill>Mermas']],['impregnado','Mermas',sl['impregnado>Mermas']]];
  const links=E.map(([s,t,v])=>({source:s,target:t,value:v,
    lineStyle:{width:w(v||0),color:(t==='Mermas')?'#cfd8dc':'#90b4d8',opacity:.65,curveness:0.05}}));
  ch.setOption({
    tooltip:{confine:true},
    series:[{type:'graph',layout:'none',roam:true,coordinateSystem:null,
      edgeSymbol:['none','arrow'],edgeSymbolSize:9,
      emphasis:{focus:'adjacency',lineStyle:{opacity:.9}},
      data:nodes,links:links}]
  },true);
}

// ---------- Gauges (aserradero) ----------
function renderGauges(){
  const ch=initChart('gauges'); const s=st('aserradero');
  function g(center,val,name,col){return{type:'gauge',center,radius:'62%',min:0,max:100,startAngle:210,endAngle:-30,
    progress:{show:true,width:10,itemStyle:{color:col}},axisLine:{lineStyle:{width:10,color:[[1,'#e6ebf2']]}},
    axisTick:{show:false},splitLine:{show:false},axisLabel:{show:false},pointer:{show:false},
    title:{offsetCenter:[0,'42%'],fontSize:11,color:'#64748b'},
    detail:{valueAnimation:true,offsetCenter:[0,'2%'],fontSize:19,fontWeight:800,color:'#27364b',formatter:'{value}%'},
    data:[{value:+(val*100).toFixed(1),name}]};}
  ch.setOption({series:[
    g(['16%','55%'],s.disp,'Disponibilidad','#2e7d32'),
    g(['38%','55%'],s.util,'Utilización','#1565c0'),
    g(['62%','55%'],s['yield'],'Yield','#00897b'),
    g(['85%','55%'],s.oee,'OEE','#ef6c00')]},true);
}

// ---------- Util vs Disp ----------
function renderUtilDisp(){
  const ch=initChart('utildisp');
  const util=STATIONS.map(n=>+(st(n).util*100).toFixed(1));
  const disp=STATIONS.map(n=>+(st(n).disp*100).toFixed(1));
  const utilCi=STATIONS.map(n=>(st(n).util_ci||0)*100), dispCi=STATIONS.map(n=>(st(n).disp_ci||0)*100);
  const errBars=(arr,ci)=>arr.map((v,i)=>[i,v-ci[i],v+ci[i]]);
  ch.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v.toFixed(1)+'%'},
    legend:{data:['Utilización','Disponibilidad'],bottom:0,itemWidth:12,textStyle:{fontSize:11}},
    grid:{left:42,right:14,top:18,bottom:40},
    xAxis:{type:'category',data:STATIONS,axisLabel:{fontSize:11}},
    yAxis:{type:'value',max:100,axisLabel:{formatter:'{value}%'}},
    series:[
      {name:'Utilización',type:'bar',data:util,itemStyle:{color:'#1565c0',borderRadius:[4,4,0,0]}},
      {name:'Disponibilidad',type:'bar',data:disp,itemStyle:{color:'#2e7d32',borderRadius:[4,4,0,0]}},
      {type:'custom',name:'IC95',data:errBars(util,utilCi),renderItem:errRender(0,STATIONS.length),tooltip:{show:false},z:5},
      {type:'custom',name:'IC95',data:errBars(disp,dispCi),renderItem:errRender(1,STATIONS.length),tooltip:{show:false},z:5},
    ]
  },true);
}
function errRender(seriesIdx,n){return function(params,api){
  const ci=api.value(0), low=api.value(1), high=api.value(2);
  const off=(seriesIdx===0?-1:1)*api.size([0,0])[0]*0.21;
  const p1=api.coord([ci,low]), p2=api.coord([ci,high]); p1[0]+=off;p2[0]+=off;
  const hw=5; const line=(x1,y1,x2,y2)=>({type:'line',shape:{x1,y1,x2,y2},style:{stroke:'#37474f',lineWidth:1.4}});
  return {type:'group',children:[line(p1[0],p1[1],p2[0],p2[1]),line(p1[0]-hw,p1[1],p1[0]+hw,p1[1]),line(p2[0]-hw,p2[1],p2[0]+hw,p2[1])]};
};}

// ---------- State composition ----------
function renderStateComp(){
  const ch=initChart('statecomp');
  const series=STATES.map(stt=>({name:stt,type:'bar',stack:'t',emphasis:{focus:'series'},
    itemStyle:{color:SC[stt]},data:STATIONS.map(n=>+st(n)[stt].toFixed(1))}));
  ch.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v.toFixed(1)+'%'},
    grid:{left:80,right:18,top:12,bottom:18},
    xAxis:{type:'value',max:100,axisLabel:{formatter:'{value}%'}},
    yAxis:{type:'category',data:STATIONS,axisLabel:{fontSize:12}},
    series
  },true);
  document.getElementById('statelegend').innerHTML=STATES.map(s=>`<span><i style="background:${SC[s]}"></i>${s}</span>`).join('');
}

// ---------- Util ranking ----------
function renderUtilRank(){
  const ch=initChart('utilrank');
  const arr=STATIONS.map(n=>({n,u:st(n).util})).sort((a,b)=>a.u-b.u);
  ch.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>(v).toFixed(1)+'%'},
    grid:{left:80,right:40,top:10,bottom:24},
    xAxis:{type:'value',max:100,axisLabel:{formatter:'{value}%'}},
    yAxis:{type:'category',data:arr.map(a=>a.n),axisLabel:{fontSize:12}},
    series:[{type:'bar',data:arr.map(a=>({value:+(a.u*100).toFixed(1),itemStyle:{color:utilColor(a.u),borderRadius:[0,5,5,0]}})),
      label:{show:true,position:'right',formatter:p=>p.value+'%',fontWeight:700,fontSize:11}}]
  },true);
}

// ---------- WIP time ----------
function renderWipTime(){
  const ch=initChart('wiptime'); const days=META.days;
  const others=BUFFERS.filter(b=>b!=='log_yard');
  const series=[{name:'log_yard (patio)',type:'line',showSymbol:false,yAxisIndex:0,
    lineStyle:{width:2.5,color:'#c62828'},areaStyle:{color:'rgba(198,40,40,.10)'},data:V.series.wip['log_yard']}];
  const pal=['#1565c0','#00897b','#8e24aa'];
  others.forEach((b,i)=>series.push({name:b,type:'line',showSymbol:false,yAxisIndex:1,
    lineStyle:{width:1.5,color:pal[i%pal.length]},data:V.series.wip[b]}));
  ch.setOption({
    tooltip:{trigger:'axis',valueFormatter:v=>fmt(v)+' m³'},
    legend:{bottom:0,itemWidth:12,textStyle:{fontSize:10}},
    grid:{left:54,right:54,top:14,bottom:42},
    xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},
    yAxis:[{type:'value',name:'patio',position:'left',axisLabel:{fontSize:10}},
           {type:'value',name:'interm.',position:'right',axisLabel:{fontSize:10}}],
    series
  },true);
}

// ---------- Arrivals vs processing ----------
function renderArrProc(){
  const ch=initChart('arrproc'); const days=META.days;
  ch.setOption({
    tooltip:{trigger:'axis',valueFormatter:v=>fmt(v,1)+' m³'},
    legend:{bottom:0,itemWidth:12,textStyle:{fontSize:11}},
    grid:{left:50,right:16,top:14,bottom:42},
    xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},
    yAxis:{type:'value',name:'m³/día'},
    series:[
      {name:'Arribos de trozos',type:'line',showSymbol:false,smooth:true,lineStyle:{width:1.4,color:'#ef6c00'},data:V.series.arrivals},
      {name:'Procesado aserradero',type:'line',showSymbol:false,smooth:true,lineStyle:{width:1.4,color:'#2e7d32'},data:V.series.aserradero_in},
    ]
  },true);
}

// ---------- Failures by station ----------
function renderFailStation(){
  const ch=initChart('failstation');
  ch.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>fmt(v,1)+'/año'},
    grid:{left:44,right:14,top:12,bottom:24},
    xAxis:{type:'category',data:STATIONS,axisLabel:{fontSize:11}},yAxis:{type:'value'},
    series:[{type:'bar',data:STATIONS.map(n=>({value:+V.failures.by_station[n].toFixed(1),
      itemStyle:{color:n==='aserradero'?'#c62828':'#1565c0',borderRadius:[4,4,0,0]}})),
      label:{show:true,position:'top',fontSize:10,formatter:p=>fmt(p.value,1)}}]
  },true);
}

// ---------- Failures classification ----------
function renderFailClass(){
  const ch=initChart('failclass'); const c=V.failures.cats;
  const data=[{name:'En turno (esperable)',value:c.en_turno,itemStyle:{color:'#2e7d32'}},
    {name:'24/7 continuo (legítimo)',value:c.cont,itemStyle:{color:'#1565c0'}},
    {name:'Overrun de lote (legítimo)',value:c.overrun,itemStyle:{color:'#fbc02d'}},
    {name:'Inicio en borde (artefacto)',value:c.borde,itemStyle:{color:'#ef6c00'}}];
  ch.setOption({
    tooltip:{trigger:'item',formatter:p=>`${p.name}<br><b>${fmt(p.value,1)}</b> (${p.percent}%)`},
    legend:{bottom:0,type:'scroll',textStyle:{fontSize:10},itemWidth:11},
    series:[{type:'pie',radius:['42%','68%'],center:['50%','44%'],avoidLabelOverlap:true,
      label:{show:false},data}]
  },true);
}

// ---------- Failures by hour ----------
function renderFailHour(){
  const ch=initChart('failhour'); const hrsArr=[...Array(24).keys()];
  ch.setOption({
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
    legend:{bottom:0,itemWidth:12,textStyle:{fontSize:10}},
    grid:{left:38,right:12,top:12,bottom:42},
    xAxis:{type:'category',data:hrsArr,name:'hora',nameTextStyle:{fontSize:10},axisLabel:{fontSize:9,interval:1}},
    yAxis:{type:'value'},
    series:[
      {name:'Turno',type:'bar',stack:'a',data:V.failures.hour_turno.map(x=>+x.toFixed(2)),itemStyle:{color:'#1565c0'},
       markArea:{itemStyle:{color:'rgba(46,125,50,.10)'},data:[[{xAxis:'7'},{xAxis:'23'}]]}},
      {name:'24/7',type:'bar',stack:'a',data:V.failures.hour_cont.map(x=>+x.toFixed(2)),itemStyle:{color:'#ef6c00'}},
    ]
  },true);
}

// ---------- Production by product ----------
function renderProdProd(){
  const ch=initChart('prodprod');
  const data=['P1','P2','P3'].map(p=>({name:p,value:+(V.production.vol[p]||0).toFixed(0),itemStyle:{color:PC[p]}}));
  ch.setOption({
    tooltip:{trigger:'item',formatter:p=>`${p.name}<br><b>${fmt(p.value)}</b> m³/año (${p.percent}%)`},
    legend:{bottom:0,itemWidth:12,textStyle:{fontSize:11}},
    series:[{type:'pie',radius:['45%','70%'],center:['50%','44%'],
      label:{show:true,formatter:p=>p.name+'\n'+fmt(p.value),fontSize:11,fontWeight:600},data}]
  },true);
}

// ---------- Throughput time ----------
function renderThroughTime(){
  const ch=initChart('throughtime'); const days=META.days;
  ch.setOption({
    tooltip:{trigger:'axis',valueFormatter:v=>fmt(v,1)+' m³'},
    grid:{left:46,right:14,top:14,bottom:30},
    xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},
    yAxis:{type:'value',name:'m³/día'},
    series:[{type:'line',showSymbol:false,smooth:true,data:V.series.throughput,
      lineStyle:{width:1.4,color:'#1565c0'},areaStyle:{color:'rgba(21,101,192,.10)'},
      markArea:{silent:true,itemStyle:{color:'rgba(198,40,40,.10)'},
        data:[[{xAxis:0,name:'warm-up'},{xAxis:META.warmup_days}]]}}]
  },true);
}

// ---------- Lead time boxplot ----------
function renderLeadBox(){
  const ch=initChart('leadbox');
  const cats=['P1','P2','P3'];
  const boxes=cats.map(p=>V.production.lead[p]); // [p5,q1,med,q3,p95]
  ch.setOption({
    tooltip:{trigger:'item',formatter:p=>{const d=p.data;return `${cats[p.dataIndex]}<br>P95: ${fmt(d[5],1)} h<br>Q3: ${fmt(d[4],1)} h<br>Mediana: <b>${fmt(d[3],1)} h</b><br>Q1: ${fmt(d[2],1)} h<br>P5: ${fmt(d[1],1)} h`;}},
    grid:{left:46,right:14,top:14,bottom:26},
    xAxis:{type:'category',data:cats},yAxis:{type:'value',name:'h'},
    series:[{type:'boxplot',data:boxes,itemStyle:{borderColor:'#1565c0',borderWidth:1.6},
      colorBy:'data'}]
  },true);
  // colorear cajas por producto
  CHARTS['leadbox'].setOption({series:[{data:boxes.map((b,i)=>({value:b,itemStyle:{color:PC[cats[i]]+'55',borderColor:PC[cats[i]]}}))}]});
}

// ---------- Table ----------
let sortField='util',sortDir='desc';
function renderTable(){
  const cols=[['station','Estación'],['tipo','Tipo'],['util','Utiliz.'],['disp','Disp.'],
    ['oee','OEE'],['mtbf','MTBF (h)'],['mttr','MTTR (h)'],['nfail','Fallas/año'],['yield','Yield']];
  const rows=[...V.stations].sort((a,b)=>{const x=a[sortField],y=b[sortField];
    if(typeof x==='string')return sortDir==='asc'?x.localeCompare(y):y.localeCompare(x);
    return sortDir==='asc'?x-y:y-x;});
  const cell=(r,f)=>{ if(f==='station')return `<b>${r.station}</b>`;
    if(f==='tipo')return `<span class="pill ${r.tipo==='24/7'?'t247':'tturno'}">${r.tipo}</span>`;
    if(['util','disp','oee','yield'].includes(f))return pct(r[f]);
    if(f==='mtbf')return fmt(r.mtbf); if(f==='mttr')return fmt(r.mttr,2); if(f==='nfail')return fmt(r.nfail,1);
    return r[f]; };
  let h='<table class="dt"><thead><tr>'+cols.map(c=>`<th data-f="${c[0]}">${c[1]}${sortField===c[0]?(sortDir==='asc'?' &#9650;':' &#9660;'):''}</th>`).join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{const bn=r.station==='aserradero'?' class="bn"':''; h+='<tr>'+cols.map(c=>`<td${c[0]==='station'?bn:''}>${cell(r,c[0])}</td>`).join('')+'</tr>';});
  h+='</tbody></table>';
  document.getElementById('tablewrap').innerHTML=h;
  document.querySelectorAll('#tablewrap th').forEach(th=>th.onclick=()=>{
    const f=th.dataset.f; if(sortField===f)sortDir=sortDir==='asc'?'desc':'asc';else{sortField=f;sortDir='desc';} renderTable();});
}

// ---------- Render all ----------
let curKey='avg';
function renderAll(){
  V=DATA.views[curKey];
  renderKPIs();renderSankey();renderGraph();renderGauges();renderUtilDisp();renderStateComp();
  renderUtilRank();renderWipTime();renderArrProc();renderFailStation();renderFailClass();
  renderFailHour();renderProdProd();renderThroughTime();renderLeadBox();renderTable();
}

// ---------- Init ----------
(function(){
  document.getElementById('methnote').innerHTML=
    `<b>Metodolog&iacute;a:</b> ${META.nreps} r&eacute;plicas independientes &middot; periodo estacionario tras warm-up de `+
    `<b>${META.warmup_days} d&iacute;as</b> (m&eacute;todo de Welch) &middot; KPIs estimados emp&iacute;ricamente de los logs de eventos &middot; `+
    `valores en m&sup3; y horas. En modo <b>Promedio</b> las barras muestran IC95% (t-Student, 4 g.l.).`;
  const sel=document.getElementById('repsel');
  sel.innerHTML='<option value="avg">Promedio (5 r&eacute;plicas)</option>'+
    [0,1,2,3,4].map(r=>`<option value="${r}">R&eacute;plica ${r}</option>`).join('');
  sel.onchange=()=>{curKey=sel.value;renderAll();};
  document.getElementById('foot').innerHTML='Aserradero CMPC Mulch&eacute;n &middot; Parte 1 &middot; generado con Python + ECharts (offline)';
  renderAll();
  window.addEventListener('resize',()=>Object.values(CHARTS).forEach(c=>c.resize()));
})();
</script>
</body>
</html>'''

html = TEMPLATE.replace("__ECHARTS__", ECHARTS).replace("__DATA__", DATA_JSON)
out = U.OUT / "dashboard.html"
out.write_text(html, encoding="utf-8")
print(f">> {out}  ({out.stat().st_size/1024:.0f} KB)")
print("   Abrir en el navegador (doble clic). Funciona offline.")
