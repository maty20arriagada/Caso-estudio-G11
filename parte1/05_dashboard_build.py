"""
05_dashboard_build.py
=================================================================
Genera el dashboard HTML autocontenido (ECharts offline) desde
output/dashboard_data.json (datos DIARIOS granulares).
El navegador recalcula todos los KPIs ante el filtro de periodo
(Año / Mes / Día) y de réplica. Incluye warm-up/convergencia,
auditoría y caja "cómo se calcula" en cada apartado.
Salida: output/dashboard.html
=================================================================
"""
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
:root{--bg:#eef1f5;--card:#fff;--head:#16243b;--head2:#22344f;--ink:#1d2733;--muted:#64748b;
--line:#e3e8ef;--accent:#1565c0;--good:#2e7d32;--warn:#ef6c00;--bad:#c62828;--gap:16px;--radius:12px;}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5;font-size:14px}
.wrap{max-width:1500px;margin:0 auto;padding:var(--gap)}
header.top{background:linear-gradient(135deg,var(--head),var(--head2));color:#fff;padding:20px 26px;border-radius:var(--radius);margin-bottom:var(--gap);box-shadow:0 4px 14px rgba(0,0,0,.12)}
header.top h1{font-size:21px;font-weight:700}
header.top .sub{font-size:12.5px;color:#aebfd6;margin-top:3px}
.controls{display:flex;gap:16px;align-items:flex-end;flex-wrap:wrap;margin-top:14px}
.cg{display:flex;flex-direction:column;gap:3px}
.cg label{font-size:10.5px;color:#aebfd6;text-transform:uppercase;letter-spacing:.5px}
.cg select{padding:7px 12px;border-radius:8px;border:1px solid #33445f;background:#0f1a2c;color:#fff;font-size:13px;font-weight:600;cursor:pointer;min-width:120px}
.cg select:disabled{opacity:.45;cursor:not-allowed}
.periodtag{margin-left:auto;font-size:12px;color:#cdd9ea;background:rgba(255,255,255,.07);padding:7px 12px;border-radius:8px;align-self:flex-end}
.note{background:#fff;border-left:4px solid var(--accent);border-radius:8px;padding:12px 16px;margin-bottom:var(--gap);font-size:12.8px;color:#475569;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.warnwin{background:#fff7ed;border-left-color:var(--warn);color:#9a3412}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.kpi{background:var(--card);border-radius:var(--radius);padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,.07);border-top:3px solid var(--accent)}
.kpi .lbl{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:600}
.kpi .val{font-size:25px;font-weight:800;margin-top:5px;line-height:1.1}
.kpi .ci{font-size:11.5px;color:var(--muted);margin-top:3px}
.kpi.red{border-top-color:var(--bad)}.kpi.green{border-top-color:var(--good)}.kpi.amber{border-top-color:var(--warn)}
.section{margin-bottom:var(--gap)}
.section h2{font-size:15px;font-weight:700;margin:6px 2px 10px;color:#0f1a2c;display:flex;align-items:center;gap:8px}
.section h2 .tag{font-size:10.5px;font-weight:700;background:#e3edfb;color:var(--accent);padding:2px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px}
.desc{font-size:12.3px;color:var(--muted);margin:0 2px 10px}
.formula{background:#f3f7fc;border-left:3px solid #90b4d8;border-radius:8px;padding:10px 14px;margin:0 2px 12px;font-size:12px;color:#33475e}
.formula .ftitle{font-weight:700;color:var(--accent);font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px}
.formula code{display:block;background:#fff;border:1px solid #e1e8f0;border-radius:5px;padding:4px 9px;margin:3px 0;font-family:'Consolas','Courier New',monospace;font-size:12px;color:#0f2c4d;white-space:pre-wrap}
.formula .mut{color:#64748b;font-size:11.5px;margin-top:6px;font-style:italic}
.grid{display:grid;gap:var(--gap)}
.g2{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.card{background:var(--card);border-radius:var(--radius);padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.card h3{font-size:13px;font-weight:700;margin-bottom:4px;color:#27364b}
.card .h3sub{font-size:11.5px;color:var(--muted);margin-bottom:8px}
.chart{width:100%;height:320px}.chart-lg{width:100%;height:430px}.chart-flow{width:100%;height:500px}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:11.5px;color:#475569;margin-top:8px}
.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.audit-summary{font-weight:800;color:var(--good);font-size:13.5px;margin-bottom:10px}
.audit-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:10px}
.audit-item{display:flex;gap:10px;align-items:flex-start;background:#fbfdff;border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.audit-badge{flex:none;font-size:10px;font-weight:800;padding:3px 8px;border-radius:20px;color:#fff;margin-top:1px}
.audit-badge.pass{background:var(--good)}.audit-badge.fail{background:var(--bad)}
.audit-name{font-weight:600;font-size:12.3px;color:#27364b}.audit-detail{color:var(--muted);font-size:11.2px;margin-top:2px}
table.dt{width:100%;border-collapse:collapse;font-size:12.5px}
table.dt th,table.dt td{padding:9px 11px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
table.dt th:first-child,table.dt td:first-child{text-align:left}
table.dt thead th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.4px;cursor:pointer;user-select:none;border-bottom:2px solid #cfd8e3}
table.dt tbody tr:hover{background:#f6f9fd}
table.dt .bn{font-weight:800;color:var(--bad)}
.footer{color:var(--muted);font-size:11.5px;text-align:center;padding:14px}
.pill{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:20px}
.pill.t247{background:#e8f0fe;color:#1a56c4}.pill.tturno{background:#fff1e6;color:#b85c00}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div><h1>Dashboard de Productividad &mdash; Aserradero CMPC Mulch&eacute;n</h1>
  <div class="sub">Caso de Estudio &middot; Parte 1: disponibilidad, cuello de botella y flujo de material &middot; Dise&ntilde;o de Sistemas de Producci&oacute;n</div></div>
  <div class="controls">
    <div class="cg"><label>Vista (r&eacute;plica)</label><select id="repsel"></select></div>
    <div class="cg"><label>A&ntilde;o</label><select id="yearsel"><option value="1">A&ntilde;o 1</option></select></div>
    <div class="cg"><label>Mes</label><select id="monthsel"></select></div>
    <div class="cg"><label>D&iacute;a</label><select id="daysel"><option value="all">Todos</option></select></div>
    <div class="periodtag" id="periodtag"></div>
  </div>
</header>

<div class="note" id="methnote"></div>
<div class="note warnwin" id="winwarn" style="display:none"></div>

<div class="kpis" id="kpis"></div>
<div class="formula" id="kpiformula"></div>

<div class="section">
  <h2><span class="tag">Estado estacionario</span> Warm-up: convergencia a r&eacute;gimen</h2>
  <div class="desc">El sistema arranca vac&iacute;o; los primeros d&iacute;as son un transitorio que se descarta. Cada curva es la salida diaria de una estaci&oacute;n, suavizada y normalizada por su media de r&eacute;gimen (1,0 = r&eacute;gimen). Franja roja = warm-up; banda verde = &plusmn;12%. (Diagn&oacute;stico fijo, no depende del filtro de periodo.)</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula (Welch)</div>
    <code>x&#772;_d = media entre r&eacute;plicas de la salida diaria &rarr; media m&oacute;vil de 7 d&iacute;as</code>
    <code>normalizado = MA(7) / media de r&eacute;gimen (d&iacute;as 150&ndash;364)</code>
    <code>fin del transitorio = 1.er d&iacute;a con |norm &minus; 1| &le; 12% sostenido 7 d&iacute;as</code>
    <code>warm-up = m&aacute;x. de los cortes por estaci&oacute;n, redondeado a semana = 14 d</code>
    <div class="mut">El WIP de log_yard crece sin acotarse (NO estacionario); por eso se usa la salida de cada estaci&oacute;n, no el WIP.</div></div>
  <div class="card"><div id="convchart" class="chart-lg"></div></div>
</div>

<div class="section">
  <h2><span class="tag">Auditor&iacute;a</span> Consistencia interna de datos y c&aacute;lculos</h2>
  <div class="desc">Cada verificaci&oacute;n cruza fuentes independientes (estados, fallas, lotes, buffers, throughput) que deben cuadrar.</div>
  <div class="card"><div id="auditwrap"></div></div>
</div>

<div class="section">
  <h2><span class="tag">Flujo</span> Flujo de material (Sankey)</h2>
  <div class="desc">Balance de materia (tasa anualizada del periodo): de los trozos a los productos terminados, con las mermas de cada etapa. Ancho de banda &prop; volumen.</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>volumen de banda = &Sigma; vol por lote en el periodo &times; 365/(d&iacute;as del periodo)</code>
    <code>merma de etapa = scrap = vol_in &minus; vol_out</code>
    <div class="mut">Balance auditado: in = out + scrap.</div></div>
  <div class="card"><div id="sankey" class="chart-flow"></div></div>
</div>

<div class="section">
  <h2><span class="tag">Flujo</span> Diagrama de la l&iacute;nea (estados, buffers y WIP)</h2>
  <div class="desc">Topolog&iacute;a del proceso. Estaciones por <b>utilizaci&oacute;n</b> (verde&rarr;rojo), buffers por <b>WIP</b>. Grosor de flecha = flujo. Hover = detalle; se arrastra y hace zoom.</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>color estaci&oacute;n = utilizaci&oacute;n (BUSY / tiempo programado) en el periodo</code>
    <code>color buffer = WIP relativo &middot; etiqueta = nivel al fin del periodo</code>
    <code>ancho de flecha &prop; flujo de material del periodo</code></div>
  <div class="card"><div id="graph" class="chart-flow"></div>
    <div class="legend">
      <span><i style="background:#2e7d32"></i>baja util.</span><span><i style="background:#fbc02d"></i>media</span>
      <span><i style="background:#c62828"></i>alta (cuello)</span><span><i style="background:#90a4ae"></i>buffer</span>
      <span><i style="background:#6d4c41"></i>trozos</span><span><i style="background:#4C72B0"></i>producto</span>
      <span><i style="background:#cfd8dc"></i>mermas</span></div></div>
</div>

<div class="section">
  <h2><span class="tag">Disponibilidad</span> Disponibilidad, utilizaci&oacute;n y confiabilidad</h2>
  <div class="desc">Indicadores del cuello de botella (gauges) y comparaci&oacute;n entre estaciones, para el periodo seleccionado.</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>tiempo programado = tiempo total &minus; OFF_SHIFT   (24/7: OFF_SHIFT = 0)</code>
    <code>Utilizaci&oacute;n = horas BUSY / tiempo programado</code>
    <code>MTBF = horas BUSY / n&ordm; fallas      (falla dependiente de la operaci&oacute;n)</code>
    <code>MTTR = media(repair_duration_h)</code>
    <code>Disponibilidad = MTBF/(MTBF+MTTR) = BUSY/(BUSY+DOWN)</code>
    <code>OEE = Disponibilidad &times; BUSY/(BUSY+SETUP) &times; Yield</code>
    <code>Yield = &Sigma; vol_out / &Sigma; vol_in</code>
    <div class="mut">El yield ~50% del aserradero es recuperaci&oacute;n estructural del aser&iacute;o, no defecto.</div></div>
  <div class="grid g2">
    <div class="card"><h3>Gauges del cuello de botella (Aserradero)</h3><div class="h3sub">la m&aacute;quina cr&iacute;tica</div><div id="gauges" class="chart"></div></div>
    <div class="card"><h3>Utilizaci&oacute;n vs Disponibilidad por estaci&oacute;n</h3><div class="h3sub">IC95% en modo Promedio</div><div id="utildisp" class="chart"></div></div>
  </div>
  <div class="card" style="margin-top:var(--gap)"><h3>Composici&oacute;n del tiempo por estado</h3><div class="h3sub">% del tiempo total</div><div id="statecomp" class="chart"></div><div class="legend" id="statelegend"></div></div>
</div>

<div class="section">
  <h2><span class="tag">Restricci&oacute;n</span> An&aacute;lisis de cuello de botella</h2>
  <div class="desc">El cuello de botella es el recurso de mayor utilizaci&oacute;n; aguas arriba se acumula WIP y aguas abajo hay inanici&oacute;n.</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>cuello = estaci&oacute;n de mayor utilizaci&oacute;n</code>
    <code>pendiente WIP = ajuste lineal del nivel diario de log_yard en el periodo</code>
    <code>arribos, procesado = m&sup3;/d&iacute;a (series diarias)</code>
    <div class="mut">BLOCKED &asymp; 0 &rArr; la restricci&oacute;n est&aacute; en la ENTRADA.</div></div>
  <div class="grid g2">
    <div class="card"><h3>Ranking de utilizaci&oacute;n</h3><div class="h3sub">identifica la restricci&oacute;n</div><div id="utilrank" class="chart"></div></div>
    <div class="card"><h3>WIP por buffer en el tiempo</h3><div class="h3sub">la banda azul marca el periodo filtrado</div><div id="wiptime" class="chart"></div></div>
  </div>
  <div class="card" style="margin-top:var(--gap)"><h3>Arribos de trozos vs capacidad de procesamiento</h3><div class="h3sub">m&sup3;/d&iacute;a</div><div id="arrproc" class="chart"></div></div>
</div>

<div class="section">
  <h2><span class="tag">Confiabilidad</span> An&aacute;lisis de fallas</h2>
  <div class="desc">Las fallas ocurren durante el procesamiento. Las "fallas fuera de horario" se explican por estaciones 24/7 y por overrun de lote.</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>cada falla se cruza con el calendario (07&ndash;23, d&iacute;a operativo) y el estado real</code>
    <code>overrun = lote iniciado EN turno que cierra pasado el horario (leg&iacute;timo)</code>
    <code>borde = lote iniciado ~2&ndash;20 min tras el cierre (artefacto)</code>
    <div class="mut">Auditado: 100% de las fallas ocurre con la m&aacute;quina en BUSY.</div></div>
  <div class="grid g3">
    <div class="card"><h3>Fallas por estaci&oacute;n</h3><div class="h3sub">tasa anual del periodo</div><div id="failstation" class="chart"></div></div>
    <div class="card"><h3>Clasificaci&oacute;n de fallas</h3><div class="h3sub">dentro/fuera de la ventana operativa</div><div id="failclass" class="chart"></div></div>
    <div class="card"><h3>Distribuci&oacute;n horaria</h3><div class="h3sub">turno vs 24/7 &middot; franja 07&ndash;23</div><div id="failhour" class="chart"></div></div>
  </div>
</div>

<div class="section">
  <h2><span class="tag">Producci&oacute;n</span> Producci&oacute;n y tiempos de ciclo</h2>
  <div class="desc">Volumen terminado por producto (tasa anualizada del periodo) y distribuci&oacute;n del lead time.</div>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>volumen por producto = &Sigma; product_outputs del periodo, anualizado</code>
    <code>lead time = exit_time &minus; salida del aserradero (no incluye espera en patio)</code>
    <code>boxplot = P5 &middot; Q1 &middot; mediana &middot; Q3 &middot; P95</code></div>
  <div class="grid g3">
    <div class="card"><h3>Producci&oacute;n por producto</h3><div class="h3sub">m&sup3;/a&ntilde;o (tasa)</div><div id="prodprod" class="chart"></div></div>
    <div class="card"><h3>Throughput diario</h3><div class="h3sub">warm-up y periodo sombreados</div><div id="throughtime" class="chart"></div></div>
    <div class="card"><h3>Lead time por producto</h3><div class="h3sub">caja=Q1-Q3, bigotes=P5-P95</div><div id="leadbox" class="chart"></div></div>
  </div>
</div>

<div class="section">
  <h2><span class="tag">Detalle</span> Tabla de KPIs por estaci&oacute;n</h2>
  <div class="formula"><div class="ftitle">C&oacute;mo se calcula</div>
    <code>columnas seg&uacute;n las secciones anteriores &middot; OEE = Disp &times; BUSY/(BUSY+SETUP) &times; Yield</code>
    <div class="mut">Clic en cualquier encabezado para ordenar.</div></div>
  <div class="card" style="overflow-x:auto"><div id="tablewrap"></div></div>
</div>

<div class="footer" id="foot"></div>
</div>

<script>
const DATA=__DATA__, META=DATA.meta, D=DATA.daily;
const SC=META.state_colors, PC=META.product_colors;
const STATIONS=META.stations, STATES=META.states, BUFFERS=META.buffers, WARM=META.warmup_days, NRE=META.nreps;
const TCRIT={1:12.706,2:4.303,3:3.182,4:2.776,5:2.571};
let CHARTS={}, V=null;
let curRep='avg', curMonth='all', curDay='all';

const fmt=(x,d=0)=>x==null||isNaN(x)?'-':x.toLocaleString('es-CL',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=(x,d=1)=>x==null||isNaN(x)?'-':(x*100).toFixed(d)+'%';
const hrs=(x,d=1)=>x==null||isNaN(x)?'-':x.toFixed(d)+' h';
function utilColor(u){u=Math.max(0,Math.min(1,u));const s=[[0,[46,125,50]],[.5,[251,192,45]],[1,[198,40,40]]];
  let a=s[0],b=s[2];for(let i=0;i<s.length-1;i++){if(u>=s[i][0]&&u<=s[i+1][0]){a=s[i];b=s[i+1];break;}}
  const t=(u-a[0])/((b[0]-a[0])||1);const c=a[1].map((v,i)=>Math.round(v+(b[1][i]-v)*t));return `rgb(${c[0]},${c[1]},${c[2]})`;}
function st(n){return V.stations.find(s=>s.station===n);}
function initChart(id){if(!CHARTS[id])CHARTS[id]=echarts.init(document.getElementById(id));return CHARTS[id];}
function repsList(){return curRep==='avg'?[0,1,2,3,4]:[+curRep];}
function sumWin(a5,r,d0,d1){let s=0;const a=a5[r];for(let d=d0;d<=d1;d++)s+=a[d];return s;}
function meanCI(v){const n=v.length;if(!n)return[null,0];const m=v.reduce((a,b)=>a+b,0)/n;
  if(n<2)return[m,0];const sd=Math.sqrt(v.reduce((s,x)=>s+(x-m)*(x-m),0)/(n-1));return[m,(TCRIT[n-1]||1.96)*sd/Math.sqrt(n)];}
function mean(v){v=v.filter(x=>x!=null);return v.length?v.reduce((a,b)=>a+b,0)/v.length:null;}
function pctls(xs){if(!xs.length)return[0,0,0,0,0];xs=xs.slice().sort((a,b)=>a-b);
  const q=p=>{const i=(xs.length-1)*p,lo=Math.floor(i),hi=Math.ceil(i);return xs[lo]+(xs[hi]-xs[lo])*(i-lo);};
  return[q(.05),q(.25),q(.5),q(.75),q(.95)];}

function curWindow(){
  let d0=0,d1=364;
  if(curMonth!=='all'){const m=META.months[+curMonth-1];d0=m.start;d1=m.end;
    if(curDay!=='all'){d0=m.start+(+curDay-1);d1=d0;}}
  const raw0=d0; let eff0=d0;
  if(d1>=WARM) eff0=Math.max(d0,WARM);   // descarta warm-up salvo que toda la ventana este dentro
  return {d0:eff0,d1,raw0,nWin:Math.max(1,d1-eff0+1),touchesWarm:raw0<WARM};
}

function computeView(){
  const reps=repsList(), W=curWindow(), {d0,d1,nWin}=W, ann=365/nWin;
  const stations=STATIONS.map(name=>{
    const cont=META.continuous.includes(name);
    const per=reps.map(r=>{
      const h={};let tot=0;STATES.forEach(s=>{const v=sumWin(D.state[name][s],r,d0,d1);h[s]=v;tot+=v;});
      const sched=tot-h.OFF_SHIFT, vin=sumWin(D.vin[name],r,d0,d1), vout=sumWin(D.vout[name],r,d0,d1);
      let nf=0,rep=0;DATA.failures.forEach(f=>{if(f[0]===r&&f[1]===name&&f[2]>=d0&&f[2]<=d1){nf++;rep+=f[5];}});
      return {h,tot,sched,vin,vout,nf,rep,util:sched>0?h.BUSY/sched:0,
        disp:(h.BUSY+h.DOWN)>0?h.BUSY/(h.BUSY+h.DOWN):1,
        mtbf:nf>0?h.BUSY/nf:null,mttr:nf>0?rep/nf:null,yld:vin>0?vout/vin:null};});
    const [util,util_ci]=meanCI(per.map(p=>p.util)), [disp,disp_ci]=meanCI(per.map(p=>p.disp));
    const mtbf=mean(per.map(p=>p.mtbf)), mttr=mean(per.map(p=>p.mttr)), yld=mean(per.map(p=>p.yld));
    const tb=per.reduce((a,p)=>a+p.h.BUSY,0), ts=per.reduce((a,p)=>a+p.h.SETUP,0);
    const oee=(disp!=null&&yld!=null)?disp*((tb+ts)>0?tb/(tb+ts):0)*yld:null;
    const o={station:name,tipo:cont?'24/7':'turno',util,util_ci,disp,disp_ci,mtbf,mttr,'yield':yld,oee,
      nfail:mean(per.map(p=>p.nf*ann))};
    STATES.forEach(s=>o[s]=mean(per.map(p=>p.tot>0?p.h[s]/p.tot*100:0)));
    return o;});
  const sankey={};META.sankey_links.forEach(ln=>sankey[ln]=mean(reps.map(r=>sumWin(D.sankey[ln],r,d0,d1)*ann)));
  const vol={},lead={};['P1','P2','P3'].forEach(p=>{
    vol[p]=mean(reps.map(r=>sumWin(D.prod[p],r,d0,d1)*ann));
    lead[p]=pctls(DATA.leads.filter(L=>reps.includes(L[0])&&L[1]===p&&L[2]>=d0&&L[2]<=d1).map(L=>L[3]));});
  const fw=DATA.failures.filter(f=>reps.includes(f[0])&&f[2]>=d0&&f[2]<=d1);
  const by_station={};STATIONS.forEach(s=>by_station[s]=fw.filter(f=>f[1]===s).length/reps.length*ann);
  const cats={en_turno:0,cont:0,overrun:0,borde:0};fw.forEach(f=>cats[f[4]]++);Object.keys(cats).forEach(k=>cats[k]/=reps.length);
  const ht=Array(24).fill(0),hc=Array(24).fill(0);
  fw.forEach(f=>{const h=Math.floor(f[3])%24;if(META.continuous.includes(f[1]))hc[h]+=1/reps.length;else ht[h]+=1/reps.length;});
  const failures={by_station,cats,hour_turno:ht,hour_cont:hc,total:fw.length/reps.length*ann};
  const ms=a5=>{const o=Array(365).fill(0);reps.forEach(r=>{for(let d=0;d<365;d++)o[d]+=a5[r][d];});return o.map(x=>x/reps.length);};
  const series={throughput:ms(D.throughput),arrivals:ms(D.arrivals),aserradero_in:ms(D.aserradero_in),wip:{}};
  BUFFERS.forEach(b=>series.wip[b]=ms(D.wip[b]));
  const ase=stations.find(s=>s.station==='aserradero');
  const [pt,ptci]=meanCI(reps.map(r=>['P1','P2','P3'].reduce((a,p)=>a+sumWin(D.prod[p],r,d0,d1),0)*ann));
  const thr=mean(reps.map(r=>sumWin(D.throughput,r,d0,d1)/nWin));
  const ly=series.wip['log_yard'];let sx=0,sy=0,sxy=0,sxx=0,n=0;
  for(let d=d0;d<=d1;d++){sx+=d;sy+=ly[d];sxy+=d*ly[d];sxx+=d*d;n++;}
  const slope=n>1?(n*sxy-sx*sy)/(n*sxx-sx*sx):0;
  const avg=curRep==='avg';
  const kpis={prod_total:pt,prod_total_ci:avg?ptci:0,throughput_dia:thr,
    util_bottleneck:ase.util,util_bottleneck_ci:avg?ase.util_ci:0,disp_bottleneck:ase.disp,disp_bottleneck_ci:avg?ase.disp_ci:0,
    yield_bottleneck:ase['yield'],oee_bottleneck:ase.oee,fallas_total:failures.total,
    logyard_slope:slope,logyard_final:ly[d1],leadtime_p3:lead.P3?lead.P3[2]:null};
  return {stations,sankey,production:{vol,lead},failures,series,kpis,window:W};
}

function renderKPIs(){const k=V.kpis,avg=(curRep==='avg');
  const cards=[
   {lbl:'Producci&oacute;n &uacute;til',val:fmt(k.prod_total)+' m&sup3;/a&ntilde;o',ci:avg&&k.prod_total_ci?('&plusmn; '+fmt(k.prod_total_ci)):'tasa anualizada',cls:'green'},
   {lbl:'Throughput l&iacute;nea',val:fmt(k.throughput_dia,1)+' m&sup3;/d&iacute;a',ci:'salida del sistema',cls:''},
   {lbl:'Utilizaci&oacute;n cuello (Aserradero)',val:pct(k.util_bottleneck),ci:avg&&k.util_bottleneck_ci?('&plusmn; '+pct(k.util_bottleneck_ci)):'',cls:'red'},
   {lbl:'Disponibilidad Aserradero',val:pct(k.disp_bottleneck),ci:avg&&k.disp_bottleneck_ci?('&plusmn; '+pct(k.disp_bottleneck_ci)):'',cls:'amber'},
   {lbl:'OEE Aserradero',val:pct(k.oee_bottleneck),ci:'disp &times; setup &times; yield',cls:'amber'},
   {lbl:'Fallas',val:fmt(k.fallas_total)+'/a&ntilde;o',ci:'tasa del periodo',cls:'red'},
   {lbl:'Backlog patio (log_yard)',val:(k.logyard_slope>=0?'+':'')+fmt(k.logyard_slope,1)+' m&sup3;/d&iacute;a',ci:'nivel '+fmt(k.logyard_final)+' m&sup3;',cls:'red'},
   {lbl:'Lead time P3 (mediana)',val:hrs(k.leadtime_p3),ci:'desde aserradero',cls:''}];
  document.getElementById('kpis').innerHTML=cards.map(c=>`<div class="kpi ${c.cls}"><div class="lbl">${c.lbl}</div><div class="val">${c.val}</div><div class="ci">${c.ci||''}</div></div>`).join('');}

function renderSankey(){const ch=initChart('sankey');
  const nc={trozos:'#6d4c41',aserradero:'#c62828',bano:'#1565c0',secado:'#1565c0',drymill:'#1565c0',impregnado:'#1565c0',Mermas:'#b0bec5',P1:PC.P1,P2:PC.P2,P3:PC.P3};
  const names=['trozos','aserradero','bano','secado','drymill','impregnado','Mermas','P1','P2','P3'];
  const nodes=names.map(n=>({name:n,itemStyle:{color:nc[n]||'#888'}}));
  const links=META.sankey_links.map(key=>{const[s,t]=key.split('>');return{source:s,target:t,value:Math.max(0,V.sankey[key]||0)};});
  ch.setOption({tooltip:{trigger:'item',triggerOn:'mousemove',formatter:p=>p.dataType==='edge'?`${p.data.source} &rarr; ${p.data.target}<br><b>${fmt(p.data.value)}</b> m&sup3;/a&ntilde;o`:`<b>${p.name}</b>`},
    series:[{type:'sankey',left:'4%',right:'9%',top:'3%',bottom:'3%',nodeWidth:16,nodeGap:14,emphasis:{focus:'adjacency'},
      lineStyle:{color:'gradient',opacity:.45,curveness:.5},label:{fontSize:12,fontWeight:600,color:'#27364b'},data:nodes,links}]},true);}

function renderGraph(){const ch=initChart('graph');
  const P={trozos:[0,0],log_yard:[120,0],aserradero:[245,0],stock_aserrado:[365,0],bano:[485,-95],P1:[610,-95],
    secado:[485,95],stock_seco:[605,95],drymill:[725,95],P2:[850,25],stock_drymill:[725,205],impregnado:[850,205],P3:[975,205],Mermas:[250,-180]};
  const nodes=[],wf={};BUFFERS.forEach(b=>wf[b]=V.series.wip[b][V.window.d1]);const mw=Math.max(...BUFFERS.map(b=>wf[b]),1);
  const tip=s=>`<b>${s.station}</b> (${s.tipo})<br>Utilizaci&oacute;n: <b>${pct(s.util)}</b><br>Disponibilidad: ${pct(s.disp)}<br>MTBF: ${fmt(s.mtbf)} h &middot; MTTR: ${fmt(s.mttr,1)} h<br>Yield: ${pct(s['yield'])} &middot; OEE: ${pct(s.oee)}<br><span style="color:#888">BUSY ${fmt(s.BUSY,0)}% IDLE ${fmt(s.IDLE,0)}% SETUP ${fmt(s.SETUP,0)}% DOWN ${fmt(s.DOWN,0)}% OFF ${fmt(s.OFF_SHIFT,0)}%</span>`;
  STATIONS.forEach(name=>{const s=st(name);nodes.push({name,x:P[name][0],y:P[name][1],symbol:'roundRect',symbolSize:[78,46],
    itemStyle:{color:utilColor(s.util),borderColor:'#fff',borderWidth:2},
    label:{show:true,formatter:`{b}\n${pct(s.util,0)}`,color:'#fff',fontWeight:700,fontSize:11,lineHeight:14},tooltip:{formatter:tip(s)}});});
  BUFFERS.forEach(b=>{const lvl=wf[b],ht=Math.min(1,lvl/mw);nodes.push({name:b,x:P[b][0],y:P[b][1],symbol:'rect',symbolSize:[58,30],
    itemStyle:{color:`rgb(${Math.round(144+(198-144)*ht)},${Math.round(164-(164-40)*ht)},${Math.round(174-(174-40)*ht)})`,borderColor:'#607d8b',borderWidth:1},
    label:{show:true,formatter:`${b.replace('stock_','').replace('log_yard','patio')}\n${fmt(lvl)} m&sup3;`,color:'#fff',fontSize:9.5,fontWeight:600,lineHeight:12},
    tooltip:{formatter:`<b>${b}</b><br>WIP al fin del periodo: <b>${fmt(lvl)}</b> m&sup3;`}});});
  [['trozos','#6d4c41'],['P1',PC.P1],['P2',PC.P2],['P3',PC.P3],['Mermas','#cfd8dc']].forEach(([n,c])=>nodes.push({name:n,x:P[n][0],y:P[n][1],symbol:'circle',symbolSize:34,
    itemStyle:{color:c,borderColor:'#fff',borderWidth:2},label:{show:true,formatter:n==='trozos'?'Trozos':n,color:n==='Mermas'?'#546e7a':'#fff',fontSize:10,fontWeight:700},tooltip:{show:n!=='trozos'&&n!=='Mermas'}}));
  const sl=V.sankey,mv=Math.max(...Object.values(sl).map(x=>x||0),1),w=v=>1+11*((v||0)/mv);
  const E=[['trozos','log_yard',sl['trozos>aserradero']],['log_yard','aserradero',sl['trozos>aserradero']],
    ['aserradero','stock_aserrado',(sl['aserradero>bano']||0)+(sl['aserradero>secado']||0)],
    ['stock_aserrado','bano',sl['aserradero>bano']],['stock_aserrado','secado',sl['aserradero>secado']],
    ['bano','P1',sl['bano>P1']],['secado','stock_seco',sl['secado>drymill']],['stock_seco','drymill',sl['secado>drymill']],
    ['drymill','P2',sl['drymill>P2']],['drymill','stock_drymill',sl['drymill>impregnado']],
    ['stock_drymill','impregnado',sl['drymill>impregnado']],['impregnado','P3',sl['impregnado>P3']],
    ['aserradero','Mermas',sl['aserradero>Mermas']],['bano','Mermas',sl['bano>Mermas']],
    ['secado','Mermas',sl['secado>Mermas']],['drymill','Mermas',sl['drymill>Mermas']],['impregnado','Mermas',sl['impregnado>Mermas']]];
  const links=E.map(([s,t,v])=>({source:s,target:t,value:v,lineStyle:{width:w(v),color:(t==='Mermas')?'#cfd8dc':'#90b4d8',opacity:.65,curveness:.05}}));
  ch.setOption({tooltip:{confine:true},series:[{type:'graph',layout:'none',roam:true,edgeSymbol:['none','arrow'],edgeSymbolSize:9,emphasis:{focus:'adjacency',lineStyle:{opacity:.9}},data:nodes,links}]},true);}

function renderGauges(){const ch=initChart('gauges'),s=st('aserradero');
  const g=(c,v,n,col)=>({type:'gauge',center:c,radius:'62%',min:0,max:100,startAngle:210,endAngle:-30,
    progress:{show:true,width:10,itemStyle:{color:col}},axisLine:{lineStyle:{width:10,color:[[1,'#e6ebf2']]}},
    axisTick:{show:false},splitLine:{show:false},axisLabel:{show:false},pointer:{show:false},
    title:{offsetCenter:[0,'42%'],fontSize:11,color:'#64748b'},
    detail:{offsetCenter:[0,'2%'],fontSize:19,fontWeight:800,color:'#27364b',formatter:'{value}%'},
    data:[{value:v==null?0:+(v*100).toFixed(1),name:n}]});
  ch.setOption({series:[g(['16%','55%'],s.disp,'Disponibilidad','#2e7d32'),g(['38%','55%'],s.util,'Utilización','#1565c0'),
    g(['62%','55%'],s['yield'],'Yield','#00897b'),g(['85%','55%'],s.oee,'OEE','#ef6c00')]},true);}

function errRender(si){return function(p,api){const ci=api.value(0),lo=api.value(1),hi=api.value(2);
  const off=(si===0?-1:1)*api.size([0,0])[0]*0.21;const p1=api.coord([ci,lo]),p2=api.coord([ci,hi]);p1[0]+=off;p2[0]+=off;
  const hw=5,L=(x1,y1,x2,y2)=>({type:'line',shape:{x1,y1,x2,y2},style:{stroke:'#37474f',lineWidth:1.4}});
  return{type:'group',children:[L(p1[0],p1[1],p2[0],p2[1]),L(p1[0]-hw,p1[1],p1[0]+hw,p1[1]),L(p2[0]-hw,p2[1],p2[0]+hw,p2[1])]};};}
function renderUtilDisp(){const ch=initChart('utildisp');
  const util=STATIONS.map(n=>+((st(n).util||0)*100).toFixed(1)),disp=STATIONS.map(n=>+((st(n).disp||0)*100).toFixed(1));
  const uci=STATIONS.map(n=>(st(n).util_ci||0)*100),dci=STATIONS.map(n=>(st(n).disp_ci||0)*100);
  const eb=(arr,ci)=>arr.map((v,i)=>[i,v-ci[i],v+ci[i]]);
  ch.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v.toFixed(1)+'%'},
    legend:{data:['Utilización','Disponibilidad'],bottom:0,itemWidth:12,textStyle:{fontSize:11}},grid:{left:42,right:14,top:18,bottom:40},
    xAxis:{type:'category',data:STATIONS,axisLabel:{fontSize:11}},yAxis:{type:'value',max:100,axisLabel:{formatter:'{value}%'}},
    series:[{name:'Utilización',type:'bar',data:util,itemStyle:{color:'#1565c0',borderRadius:[4,4,0,0]}},
      {name:'Disponibilidad',type:'bar',data:disp,itemStyle:{color:'#2e7d32',borderRadius:[4,4,0,0]}},
      {type:'custom',data:eb(util,uci),renderItem:errRender(0),tooltip:{show:false},z:5},
      {type:'custom',data:eb(disp,dci),renderItem:errRender(1),tooltip:{show:false},z:5}]},true);}

function renderStateComp(){const ch=initChart('statecomp');
  const series=STATES.map(s=>({name:s,type:'bar',stack:'t',emphasis:{focus:'series'},itemStyle:{color:SC[s]},data:STATIONS.map(n=>+(st(n)[s]||0).toFixed(1))}));
  ch.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v.toFixed(1)+'%'},grid:{left:80,right:18,top:12,bottom:18},
    xAxis:{type:'value',max:100,axisLabel:{formatter:'{value}%'}},yAxis:{type:'category',data:STATIONS,axisLabel:{fontSize:12}},series},true);
  document.getElementById('statelegend').innerHTML=STATES.map(s=>`<span><i style="background:${SC[s]}"></i>${s}</span>`).join('');}

function renderUtilRank(){const ch=initChart('utilrank');
  const arr=STATIONS.map(n=>({n,u:st(n).util||0})).sort((a,b)=>a.u-b.u);
  ch.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v.toFixed(1)+'%'},grid:{left:80,right:40,top:10,bottom:24},
    xAxis:{type:'value',max:100,axisLabel:{formatter:'{value}%'}},yAxis:{type:'category',data:arr.map(a=>a.n),axisLabel:{fontSize:12}},
    series:[{type:'bar',data:arr.map(a=>({value:+(a.u*100).toFixed(1),itemStyle:{color:utilColor(a.u),borderRadius:[0,5,5,0]}})),
      label:{show:true,position:'right',formatter:p=>p.value+'%',fontWeight:700,fontSize:11}}]},true);}

function winMark(extra){const w=V.window;const data=extra?extra.slice():[];
  if(!(w.d0<=WARM&&w.d1>=364))data.push([{xAxis:w.d0,itemStyle:{color:'rgba(21,101,192,.10)'}},{xAxis:w.d1}]);
  return data.length?{silent:true,data}:undefined;}

function renderWipTime(){const ch=initChart('wiptime'),days=META.days,others=BUFFERS.filter(b=>b!=='log_yard');
  const series=[{name:'log_yard (patio)',type:'line',showSymbol:false,yAxisIndex:0,lineStyle:{width:2.5,color:'#c62828'},
    areaStyle:{color:'rgba(198,40,40,.10)'},data:V.series.wip['log_yard'],markArea:winMark()}];
  const pal=['#1565c0','#00897b','#8e24aa'];
  others.forEach((b,i)=>series.push({name:b,type:'line',showSymbol:false,yAxisIndex:1,lineStyle:{width:1.5,color:pal[i%3]},data:V.series.wip[b]}));
  ch.setOption({tooltip:{trigger:'axis',valueFormatter:v=>fmt(v)+' m³'},legend:{bottom:0,itemWidth:12,textStyle:{fontSize:10}},
    grid:{left:54,right:54,top:14,bottom:42},xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},
    yAxis:[{type:'value',name:'patio',axisLabel:{fontSize:10}},{type:'value',name:'interm.',position:'right',axisLabel:{fontSize:10}}],series},true);}

function renderArrProc(){const ch=initChart('arrproc'),days=META.days;
  ch.setOption({tooltip:{trigger:'axis',valueFormatter:v=>fmt(v,1)+' m³'},legend:{bottom:0,itemWidth:12,textStyle:{fontSize:11}},
    grid:{left:50,right:16,top:14,bottom:42},xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},yAxis:{type:'value',name:'m³/día'},
    series:[{name:'Arribos de trozos',type:'line',showSymbol:false,smooth:true,lineStyle:{width:1.4,color:'#ef6c00'},data:V.series.arrivals,markArea:winMark()},
      {name:'Procesado aserradero',type:'line',showSymbol:false,smooth:true,lineStyle:{width:1.4,color:'#2e7d32'},data:V.series.aserradero_in}]},true);}

function renderFailStation(){const ch=initChart('failstation');
  ch.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>fmt(v,1)+'/año'},grid:{left:44,right:14,top:12,bottom:24},
    xAxis:{type:'category',data:STATIONS,axisLabel:{fontSize:11}},yAxis:{type:'value'},
    series:[{type:'bar',data:STATIONS.map(n=>({value:+(V.failures.by_station[n]||0).toFixed(1),itemStyle:{color:n==='aserradero'?'#c62828':'#1565c0',borderRadius:[4,4,0,0]}})),
      label:{show:true,position:'top',fontSize:10,formatter:p=>fmt(p.value,1)}}]},true);}

function renderFailClass(){const ch=initChart('failclass'),c=V.failures.cats;
  const data=[{name:'En turno (esperable)',value:c.en_turno,itemStyle:{color:'#2e7d32'}},{name:'24/7 continuo (legítimo)',value:c.cont,itemStyle:{color:'#1565c0'}},
    {name:'Overrun de lote (legítimo)',value:c.overrun,itemStyle:{color:'#fbc02d'}},{name:'Inicio en borde (artefacto)',value:c.borde,itemStyle:{color:'#ef6c00'}}];
  ch.setOption({tooltip:{trigger:'item',formatter:p=>`${p.name}<br><b>${fmt(p.value,1)}</b> (${p.percent}%)`},legend:{bottom:0,type:'scroll',textStyle:{fontSize:10},itemWidth:11},
    series:[{type:'pie',radius:['42%','68%'],center:['50%','44%'],avoidLabelOverlap:true,label:{show:false},data}]},true);}

function renderFailHour(){const ch=initChart('failhour'),H=[...Array(24).keys()];
  ch.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},legend:{bottom:0,itemWidth:12,textStyle:{fontSize:10}},grid:{left:38,right:12,top:12,bottom:42},
    xAxis:{type:'category',data:H,name:'hora',nameTextStyle:{fontSize:10},axisLabel:{fontSize:9,interval:1}},yAxis:{type:'value'},
    series:[{name:'Turno',type:'bar',stack:'a',data:V.failures.hour_turno.map(x=>+x.toFixed(2)),itemStyle:{color:'#1565c0'},markArea:{itemStyle:{color:'rgba(46,125,50,.10)'},data:[[{xAxis:'7'},{xAxis:'23'}]]}},
      {name:'24/7',type:'bar',stack:'a',data:V.failures.hour_cont.map(x=>+x.toFixed(2)),itemStyle:{color:'#ef6c00'}}]},true);}

function renderProdProd(){const ch=initChart('prodprod');
  const data=['P1','P2','P3'].map(p=>({name:p,value:+(V.production.vol[p]||0).toFixed(0),itemStyle:{color:PC[p]}}));
  ch.setOption({tooltip:{trigger:'item',formatter:p=>`${p.name}<br><b>${fmt(p.value)}</b> m³/año (${p.percent}%)`},legend:{bottom:0,itemWidth:12,textStyle:{fontSize:11}},
    series:[{type:'pie',radius:['45%','70%'],center:['50%','44%'],label:{show:true,formatter:p=>p.name+'\n'+fmt(p.value),fontSize:11,fontWeight:600},data}]},true);}

function renderThroughTime(){const ch=initChart('throughtime'),days=META.days;
  ch.setOption({tooltip:{trigger:'axis',valueFormatter:v=>fmt(v,1)+' m³'},grid:{left:46,right:14,top:14,bottom:30},
    xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},yAxis:{type:'value',name:'m³/día'},
    series:[{type:'line',showSymbol:false,smooth:true,data:V.series.throughput,lineStyle:{width:1.4,color:'#1565c0'},areaStyle:{color:'rgba(21,101,192,.10)'},
      markArea:winMark([[{xAxis:0,name:'warm-up',itemStyle:{color:'rgba(198,40,40,.10)'}},{xAxis:WARM}]])}]},true);}

function renderLeadBox(){const ch=initChart('leadbox'),cats=['P1','P2','P3'],boxes=cats.map(p=>V.production.lead[p]);
  ch.setOption({tooltip:{trigger:'item',formatter:p=>{const d=boxes[p.dataIndex];return `${cats[p.dataIndex]}<br>P95: ${fmt(d[4],1)} h<br>Q3: ${fmt(d[3],1)} h<br>Mediana: <b>${fmt(d[2],1)} h</b><br>Q1: ${fmt(d[1],1)} h<br>P5: ${fmt(d[0],1)} h`;}},
    grid:{left:46,right:14,top:14,bottom:26},xAxis:{type:'category',data:cats},yAxis:{type:'value',name:'h'},
    series:[{type:'boxplot',data:boxes.map((b,i)=>({value:b,itemStyle:{color:PC[cats[i]]+'55',borderColor:PC[cats[i]],borderWidth:1.6}}))}]},true);}

let sortField='util',sortDir='desc';
function renderTable(){const cols=[['station','Estación'],['tipo','Tipo'],['util','Utiliz.'],['disp','Disp.'],['oee','OEE'],['mtbf','MTBF (h)'],['mttr','MTTR (h)'],['nfail','Fallas/año'],['yield','Yield']];
  const rows=[...V.stations].sort((a,b)=>{const x=a[sortField],y=b[sortField];if(typeof x==='string')return sortDir==='asc'?x.localeCompare(y):y.localeCompare(x);
    return sortDir==='asc'?((x||0)-(y||0)):((y||0)-(x||0));});
  const cell=(r,f)=>{if(f==='station')return `<b>${r.station}</b>`;if(f==='tipo')return `<span class="pill ${r.tipo==='24/7'?'t247':'tturno'}">${r.tipo}</span>`;
    if(['util','disp','oee','yield'].includes(f))return pct(r[f]);if(f==='mtbf')return fmt(r.mtbf);if(f==='mttr')return fmt(r.mttr,2);if(f==='nfail')return fmt(r.nfail,1);return r[f];};
  let h='<table class="dt"><thead><tr>'+cols.map(c=>`<th data-f="${c[0]}">${c[1]}${sortField===c[0]?(sortDir==='asc'?' &#9650;':' &#9660;'):''}</th>`).join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{const bn=r.station==='aserradero'?' class="bn"':'';h+='<tr>'+cols.map(c=>`<td${c[0]==='station'?bn:''}>${cell(r,c[0])}</td>`).join('')+'</tr>';});
  document.getElementById('tablewrap').innerHTML=h+'</tbody></table>';
  document.querySelectorAll('#tablewrap th').forEach(th=>th.onclick=()=>{const f=th.dataset.f;if(sortField===f)sortDir=sortDir==='asc'?'desc':'asc';else{sortField=f;sortDir='desc';}renderTable();});}

function renderConvergencia(){const C=META.convergencia;if(!C||!C.norm)return;const ch=initChart('convchart'),days=C.days;
  const pal={'LINEA (throughput)':'#111','aserradero':'#c62828','bano':'#1565c0','secado':'#ef6c00','drymill':'#6a1b9a','impregnado':'#00897b'};
  const series=Object.keys(C.norm).map(name=>({name:name+(C.cuts&&C.cuts[name]!=null?` (corte ${C.cuts[name]}d)`:''),type:'line',showSymbol:false,emphasis:{focus:'series'},
    lineStyle:{width:name.indexOf('LINEA')>=0?3:1.4,color:pal[name]||'#888'},data:C.norm[name]}));
  if(series.length){series[0].markArea={silent:true,itemStyle:{color:'rgba(198,40,40,.10)'},data:[[{xAxis:0,name:'warm-up '+C.warmup_days+' d'},{xAxis:C.warmup_days}]]};
    series[0].markLine={silent:true,symbol:'none',lineStyle:{color:'#2e7d32',type:'dotted'},data:[{yAxis:1.12},{yAxis:.88},{yAxis:1}]};}
  ch.setOption({tooltip:{trigger:'axis',valueFormatter:v=>(+v).toFixed(2)},legend:{bottom:0,type:'scroll',textStyle:{fontSize:10},itemWidth:12},
    grid:{left:52,right:18,top:16,bottom:54},xAxis:{type:'category',data:days,name:'día',axisLabel:{fontSize:10}},
    yAxis:{type:'value',name:'salida / media régimen',min:0,max:1.6},dataZoom:[{type:'slider',startValue:0,endValue:90,height:16,bottom:30},{type:'inside'}],series},true);}

function renderAudit(){const A=META.audit,el=document.getElementById('auditwrap');if(!A||!A.checks){el.innerHTML='(sin datos)';return;}
  el.innerHTML=`<div class="audit-summary">&#10004; ${A.npass}/${A.ntotal} verificaciones de consistencia superadas &middot; warm-up ${A.warmup_days} d</div>`+
    '<div class="audit-grid">'+A.checks.map(c=>`<div class="audit-item"><span class="audit-badge ${c.status==='PASS'?'pass':'fail'}">${c.status}</span><div><div class="audit-name">${c.name}</div><div class="audit-detail">${c.detail}</div></div></div>`).join('')+'</div>';}

function renderKpiFormula(){document.getElementById('kpiformula').innerHTML='<div class="ftitle">C&oacute;mo se calculan los KPIs (sobre el periodo filtrado)</div>'+
  '<code>Producci&oacute;n &uacute;til = &Sigma;(P1,P2,P3) del periodo &times; 365/(d&iacute;as) &middot; Throughput = vol terminado / d&iacute;as</code>'+
  '<code>Backlog patio = pendiente lineal del nivel de log_yard en el periodo</code>'+
  '<div class="mut">En modo Promedio se reporta &plusmn; IC95% (t-Student). Las m&eacute;tricas siempre excluyen el warm-up.</div>';}

function updatePeriodUI(){
  const tag=document.getElementById('periodtag'),warn=document.getElementById('winwarn'),w=V.window;
  let label;
  if(curMonth==='all')label=`A&ntilde;o completo &middot; d&iacute;as ${w.d0}&ndash;${w.d1} (post warm-up) &middot; ${w.nWin} d&iacute;as`;
  else{const m=META.months[+curMonth-1];label=(curDay==='all'?m.name:`${m.name} d&iacute;a ${curDay}`)+` &middot; d&iacute;as ${w.d0}&ndash;${w.d1} &middot; ${w.nWin} d&iacute;a(s)`;}
  tag.innerHTML='&#128197; '+label;
  if(w.nWin<10||w.touchesWarm){warn.style.display='block';
    warn.innerHTML='&#9888; Ventana corta o solapada con el warm-up: las m&eacute;tricas de confiabilidad (MTBF, disponibilidad) y el lead time pueden ser poco representativos en periodos breves.';}
  else warn.style.display='none';}

function renderAll(){V=computeView();renderKPIs();renderSankey();renderGraph();renderGauges();renderUtilDisp();
  renderStateComp();renderUtilRank();renderWipTime();renderArrProc();renderFailStation();renderFailClass();
  renderFailHour();renderProdProd();renderThroughTime();renderLeadBox();renderTable();updatePeriodUI();}

(function(){
  const A=META.audit||{};
  document.getElementById('methnote').innerHTML=`<b>Metodolog&iacute;a:</b> ${META.nreps} r&eacute;plicas &middot; warm-up <b>${META.warmup_days} d&iacute;as</b> (Welch, auditado) &middot; KPIs emp&iacute;ricos de los logs &middot; filtro de periodo (A&ntilde;o/Mes/D&iacute;a) recalcula todo en el navegador &middot; <b style="color:#2e7d32">auditor&iacute;a ${A.npass||'-'}/${A.ntotal||'-'} PASS</b>.`;
  const rs=document.getElementById('repsel');rs.innerHTML='<option value="avg">Promedio (5 r&eacute;plicas)</option>'+[0,1,2,3,4].map(r=>`<option value="${r}">R&eacute;plica ${r}</option>`).join('');
  const msel=document.getElementById('monthsel');msel.innerHTML='<option value="all">Todos</option>'+META.months.map(m=>`<option value="${m.idx}">${m.name}</option>`).join('');
  const dsel=document.getElementById('daysel');
  function fillDays(){if(curMonth==='all'){dsel.innerHTML='<option value="all">Todos</option>';dsel.disabled=true;return;}
    const m=META.months[+curMonth-1];dsel.disabled=false;dsel.innerHTML='<option value="all">Todos</option>'+Array.from({length:m.ndays},(_,i)=>`<option value="${i+1}">${i+1}</option>`).join('');}
  fillDays();
  rs.onchange=()=>{curRep=rs.value;renderAll();};
  msel.onchange=()=>{curMonth=msel.value;curDay='all';fillDays();renderAll();};
  dsel.onchange=()=>{curDay=dsel.value;renderAll();};
  document.getElementById('foot').innerHTML='Aserradero CMPC Mulch&eacute;n &middot; Parte 1 &middot; Python + ECharts (offline)';
  renderKpiFormula();renderConvergencia();renderAudit();renderAll();
  window.addEventListener('resize',()=>Object.values(CHARTS).forEach(c=>c.resize()));
})();
</script>
</body>
</html>'''

html = TEMPLATE.replace("__ECHARTS__", ECHARTS).replace("__DATA__", DATA_JSON)
out = U.OUT / "dashboard.html"
out.write_text(html, encoding="utf-8")
print(f">> {out}  ({out.stat().st_size/1024:.0f} KB)")
