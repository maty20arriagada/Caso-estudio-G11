"""
build_dashboard.py
=========================================================================
Genera el dashboard HTML autocontenido para la Parte 2:
Distribucion optima de madera desde CMPC Mulchen.

- Mapa Leaflet interactivo con rutas y volumenes
- Grafico Sankey (ECharts)
- KPIs: costo total, costo/km, cumplimiento de minimos
- Tabla de despachos optimos

Salida: parte2/output/dashboard_distribucion.html
=========================================================================
"""

from pathlib import Path

PARTE2 = Path(__file__).resolve().parent
BASE = PARTE2.parent
OUT = PARTE2 / "output"
OUT.mkdir(parents=True, exist_ok=True)

SOLUTION_JSON = (PARTE2 / "solucion_distribucion.json").read_text(encoding="utf-8")
ECHARTS_JS = (BASE / "parte1" / "vendor" / "echarts.min.js").read_text(encoding="utf-8")

HTML = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Distribucion — CMPC Mulchen (Parte 2)</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E🚚%3C/text%3E%3C/svg%3E">
<script>{ECHARTS_JS}</script>
<style>
:root{{--bg:#eef1f5;--card:#fff;--head:#16243b;--head2:#22344f;--ink:#1d2733;--muted:#64748b;
--line:#e3e8ef;--accent:#1565c0;--good:#2e7d32;--warn:#ef6c00;--bad:#c62828;--gap:16px;--radius:12px;
--shadow-sm:0 1px 3px rgba(0,0,0,.06);--shadow-md:0 4px 14px rgba(0,0,0,.1);--shadow-lg:0 8px 30px rgba(0,0,0,.12);
--transition:.2s ease;}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5;font-size:14px;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1500px;margin:0 auto;padding:var(--gap)}}
header.top{{background:linear-gradient(135deg,var(--head),var(--head2));color:#fff;padding:20px 26px;border-radius:var(--radius);margin-bottom:var(--gap);box-shadow:var(--shadow-md)}}
header.top h1{{font-size:22px;font-weight:800;letter-spacing:-.3px}}
header.top .sub{{font-size:12.5px;color:#aebfd6;margin-top:3px;opacity:.85}}
.controls{{display:flex;gap:14px;align-items:flex-end;flex-wrap:wrap;margin-top:14px}}
.cg{{display:flex;flex-direction:column;gap:3px}}
.cg label{{font-size:10.5px;color:#aebfd6;text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
.cg select{{padding:7px 12px;border-radius:8px;border:1px solid #33445f;background:#0f1a2c;color:#fff;font-size:13px;font-weight:600;cursor:pointer;min-width:128px;transition:border var(--transition)}}
.cg select:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px rgba(21,101,192,.3)}}
.periodtag{{margin-left:auto;font-size:12px;color:#cdd9ea;background:rgba(255,255,255,.07);padding:7px 12px;border-radius:8px;align-self:flex-end;backdrop-filter:blur(4px)}}
.note{{background:#fff;border-left:4px solid var(--accent);border-radius:8px;padding:12px 16px;margin-bottom:var(--gap);font-size:12.8px;color:#475569;box-shadow:var(--shadow-sm)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:var(--gap);margin-bottom:var(--gap)}}
.kpi{{background:var(--card);border-radius:var(--radius);padding:15px 17px;box-shadow:var(--shadow-sm);border-top:3px solid var(--accent);transition:transform var(--transition),box-shadow var(--transition)}}
.kpi:hover{{transform:translateY(-2px);box-shadow:var(--shadow-md)}}
.kpi .lbl{{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:600}}
.kpi .val{{font-size:22px;font-weight:800;margin-top:5px;line-height:1.1}}
.kpi .ci{{font-size:11px;color:var(--muted);margin-top:3px}}
.kpi.green{{border-top-color:var(--good)}}.kpi.amber{{border-top-color:var(--warn)}}
.section{{margin-bottom:var(--gap)}}
.section h2{{font-size:15px;font-weight:700;margin:6px 2px 10px;color:#0f1a2c;display:flex;align-items:center;gap:8px}}
.section h2 .tag{{font-size:10.5px;font-weight:700;background:#e3edfb;color:var(--accent);padding:2px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px}}
.desc{{font-size:12.3px;color:var(--muted);margin:0 2px 10px}}
.formula{{background:#f3f7fc;border-left:3px solid #90b4d8;border-radius:8px;padding:10px 14px;margin:0 2px 12px;font-size:12px;color:#33475e;transition:box-shadow var(--transition)}}
.formula code{{display:block;background:#fff;border:1px solid #e1e8f0;border-radius:5px;padding:4px 9px;margin:3px 0;font-family:'SFMono-Regular','Consolas','Liberation Mono',Menlo,monospace;font-size:12px;color:#0f2c4d;white-space:pre-wrap}}
.grid{{display:grid;gap:var(--gap)}}
.g2{{grid-template-columns:repeat(auto-fit,minmax(460px,1fr))}}
.card{{background:var(--card);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow-sm);transition:box-shadow var(--transition)}}
.card:hover{{box-shadow:var(--shadow-md)}}
.card h3{{font-size:13px;font-weight:700;margin-bottom:4px;color:#27364b}}
.chart{{width:100%;height:380px}}.chart-lg{{width:100%;height:480px}}
.maplg{{width:100%;height:500px;border-radius:var(--radius);border:2px solid var(--line)}}
.map-fallback{{display:flex;align-items:center;justify-content:center;width:100%;height:500px;background:#f4f7fc;border-radius:var(--radius);color:var(--muted);font-size:13px;flex-direction:column;gap:8px}}
table.tbl{{width:100%;border-collapse:collapse;font-size:13px}}
table.tbl thead{{background:#f4f7fc}}
table.tbl th{{text-align:left;padding:10px 12px;font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:600;border-bottom:2px solid var(--line)}}
table.tbl td{{padding:9px 12px;border-bottom:1px solid var(--line)}}
table.tbl tbody tr:hover{{background:#f8fafe}}
.badge{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700}}
.badge.p1{{background:#e3f2fd;color:#1565c0}}
.badge.p2{{background:#e8f5e9;color:#2e7d32}}
.badge.p3{{background:#fff3e0;color:#ef6c00}}
#foot{{text-align:center;font-size:11.5px;color:var(--muted);padding:20px 0 10px;border-top:1px solid var(--line);margin-top:var(--gap)}}
#loader{{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:var(--card);padding:20px 36px;border-radius:var(--radius);box-shadow:var(--shadow-lg);z-index:9999;font-weight:700;font-size:14px;display:none}}
</style>
</head>
<body>
<div id="loader">Cargando dashboard...</div>
<div class="wrap">
<header class="top">
<h1>Distribucion Optima — CMPC Mulchen</h1>
<div class="sub">Parte 2 · Programacion Lineal (PuLP + CBC) · Minimizacion de costo de transporte</div>
<div class="controls">
<div class="cg"><label>Replica</label><select id="repsel"><option value="avg">Promedio 5 replicas</option></select></div>
<div class="cg"><label>Producto</label><select id="prodsel"><option value="all">Todos (P1+P2+P3)</option><option value="P1">P1 — Mad. verde tratada</option><option value="P2">P2 — Mad. seca clasificada</option><option value="P3">P3 — Mad. impregnada</option></select></div>
<div class="cg"><label>Destino / Ruta</label><select id="destsel"><option value="all">Todos los destinos</option></select></div>
<div class="periodtag" id="filtertag"></div>
</div>
</header>
<div class="note">
<b>Metodologia:</b> Modelo de transporte con minimos contractuales y capacidades maximas por destino-producto. Resuelto con PuLP (CBC solver). Las distancias provienen de rutas reales extraidas de Google Earth (KML). Costo unitario: $100 CLP/(m³·km).<br>
<b>Conexion Parte 1:</b> La produccion disponible (P1, P2, P3) proviene del analisis de productividad del Aserradero CMPC Mulchen — <em>RESUMEN_PARTE1.md</em>. Total produccion asignada: <span id="parte1vol"></span> m³/año.
</div>

<div class="kpis" id="kpirow"></div>

<div class="section">
<h2><span class="tag">Mapa</span> Rutas y Despachos</h2>
<div class="desc">Rutas reales de Google Earth. Grosor proporcional al volumen despachado. <em>(Requiere internet para cargar losetas.)</em></div>
<div class="card" style="padding:0;overflow:hidden"><div id="map-container"><div id="map" class="maplg"></div></div></div>
</div>

<div class="grid g2">
<div class="card"><h3>Flujo Mulchen → Destinos (m³)</h3><div id="sankey" class="chart-lg"></div></div>
<div class="card"><h3>Viajes de Camion → Destinos</h3><div id="trucksankey" class="chart-lg"></div></div>
</div>

<div class="grid g2">
<div class="card"><h3>Volumen despachado por Destino y Producto</h3><div id="stackbar" class="chart"></div></div>
<div class="card"><h3>Desglose de Costos por Destino</h3><div id="costbar" class="chart"></div></div>
</div>

<div class="grid g2">
<div class="card"><h3>Distancia vs Volumen</h3><div id="scatter" class="chart"></div></div>
<div class="card"><h3>Viajes de camion por Destino</h3><div id="truckchart" class="chart"></div></div>
</div>

<div class="section">
<h2><span class="tag">Detalle</span> Plan Optimo de Despachos</h2>
<div class="card">
<div style="overflow-x:auto">
<table class="tbl" id="detailtbl"><thead><tr><th>Destino</th><th>Prod</th><th>Dist (km)</th><th>Vol (m³)</th><th>Costo transp. (CLP)</th><th>Costo/m³</th><th>Camiones (viajes)</th><th>Costo camion</th><th>Costo tren est.</th></tr></thead><tbody></tbody></table>
</div>
</div>
</div>

<div class="section">
<h2><span class="tag">Transporte</span> Analisis Multimodal</h2>
<div class="desc">Comparacion tractocamion vs ferrocarril para las rutas del plan optimo.</div>
<div class="card" style="margin-bottom:var(--gap)"><h3>Costo acumulado: Camion vs Tren</h3><div id="modalchart" class="chart"></div></div>
<div class="card" style="margin-top:var(--gap)">
<h3>Supuestos del analisis</h3>
<div class="formula">
<div class="ftitle">Tractocamion</div>
<code>Capacidad: 30 m³/viaje (tractocamion 6x4 + semirremolque 3 ejes, estandar forestal chileno)
Costo: $1.200 CLP/km + $50.000 CLP fijo por viaje
Fuente: tarifas de referencia flete forestalRegion del Biobio (2024)</code>
<div class="ftitle" style="margin-top:10px">Ferrocarril (FEPASA / TRANSAP)</div>
<code>Costo: ~$30 CLP/(m³·km) + $3.500 CLP/m³ de transbordo en Laja
Aplicable a: Puerto Coronel, San Vicente, Lirquen, Reman Coronel (cercanos a la via ferrea)
No aplicable a: Collipulli, Los Angeles (sin conexion ferroviaria competitiva)
Nota: Requiere transbordo camion→tren en estacion Laja (~30 km desde Mulchen).</code>
</div>
</div>
</div>

<div class="section">
<h2><span class="tag">Formulas</span> Modelo Matematico</h2>
<div class="formula">
<code>
min &Sigma;<sub>i</sub> &Sigma;<sub>j</sub> 100 · d<sub>i</sub> · x<sub>ij</sub>

s.a.:
&Sigma;<sub>i</sub> x<sub>ij</sub> = P<sub>j</sub>           &forall;j  (toda la produccion debe distribuirse)
L<sub>ij</sub> &le; x<sub>ij</sub> &le; U<sub>ij</sub>    &forall;i,j (minimo contractual y capacidad maxima)
x<sub>ij</sub> &ge; 0                       (no negatividad)
</code>
<p style="margin-top:8px;font-size:11.5px;color:var(--muted)">
<i>d<sub>i</sub></i>: distancia Mulchen → destino i [km] (Haversine, rutas Google Earth)<br>
<i>P<sub>j</sub></i>: produccion disponible de P<sub>j</sub> [m³/ano] (Parte 1)<br>
<i>L<sub>ij</sub>, U<sub>ij</sub></i>: limites contractuales [m³/ano] (Caso de Estudio)
</p>
</div>
</div>

<div id="foot">CMPC Mulchen &middot; Parte 2 &middot; Distribucion Optima &middot; Python + PuLP + ECharts</div>
</div>

<script>
const SOL = {SOLUTION_JSON};
const CH = {{}};
const COLORS = {{P1:'#1565c0',P2:'#2e7d32',P3:'#ef6c00'}};
var curReplica='avg',curProduct='all',curDest='all';
var mapInstance=null;

function fmt(n){{return n.toLocaleString('es-CL',{{minimumFractionDigits:0,maximumFractionDigits:0}});}}
function fmt2(n){{return n.toLocaleString('es-CL',{{minimumFractionDigits:2,maximumFractionDigits:2}});}}
function safeCall(fn,name){{try{{fn();}}catch(e){{console.error('Error en '+name+':',e);}}}}

function getDS(){{return (curReplica==='avg')?SOL:SOL.replicas[curReplica]||SOL;}}

function getFilteredData(){{
  var ds=getDS();var deps=ds.despachos||SOL.despachos;
  return deps.filter(function(d){{
    if(curProduct!=='all'&&d.producto!==curProduct)return false;
    if(curDest!=='all'&&d.destino!==curDest)return false;
    return true;
  }});
}}

function getTransporte(){{
  var ds=getDS();return ds.transporte||SOL.transporte||{{}};
}}

function updateFilterUI(){{
  var tag=document.getElementById('filtertag'),parts=[];
  if(curReplica!=='avg')parts.push('Replica '+curReplica);
  if(curProduct!=='all')parts.push('Producto: '+curProduct);
  if(curDest!=='all'){{var dn=SOL.destinos[curDest].nombre;parts.push('Destino: '+dn);}}
  if(parts.length===0)parts.push('Sin filtros activos');
  tag.innerHTML='&#128269; '+parts.join(' &middot; ');
}}

function renderKPIs(){{
  var deps=getFilteredData();
  var totalVol=0,totalCost=0,weightedDist=0,nDesp=0;
  deps.forEach(function(d){{totalVol+=d.volumen_m3;totalCost+=d.costo_clp;weightedDist+=d.distancia_km*d.volumen_m3;nDesp++;}});
  var avgDist=totalVol>0?weightedDist/totalVol:0;
  var costPerM3=totalVol>0?totalCost/totalVol:0;

  var allVol=0;(SOL.despachos||[]).forEach(function(d){{allVol+=d.volumen_m3;}});
  var volPct=allVol>0?(totalVol/allVol*100).toFixed(0):'0';

  var repLabel=(curReplica==='avg')?'Promedio 5 replicas':'Replica '+curReplica;

  var items=[
    ['Costo Total','$'+fmt(totalCost)+' CLP','filtrado: '+volPct+'% del vol.','green'],
    ['Despachos',''+nDesp,'rutas activas filtradas',''],
    ['Costo / m³','$'+fmt2(costPerM3)+' CLP/m³','promedio ponderado',''],
    ['Distancia media',''+fmt2(avgDist)+' km','volumen ponderado',''],
    ['Volumen',''+fmt(totalVol)+' m³/ano',repLabel,'amber'],
  ];
  document.getElementById('kpirow').innerHTML=items.map(function(i){{
    return '<div class="kpi '+i[3]+'"><div class="lbl">'+i[0]+'</div><div class="val">'+i[1]+'</div><div class="ci">'+i[2]+'</div></div>';
  }}).join('');
  var p1el=document.getElementById('parte1vol');
  if(p1el)p1el.textContent=fmt(totalVol);
  updateFilterUI();
}}

function loadLeaflet(cb,msec){{
  msec=msec||8000;
  if(typeof L!=='undefined'){{cb();return;}}
  if(document.getElementById('leaf-css')){{waitL();return;}}
  var css=document.createElement('link');css.id='leaf-css';css.rel='stylesheet';
  css.href='https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css';
  css.onerror=tryAltCDN;
  document.head.appendChild(css);
  var js=document.createElement('script');js.id='leaf-js';
  js.src='https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js';
  js.onload=cb;js.onerror=tryAltCDN;
  document.head.appendChild(js);
  var t=setTimeout(function(){{if(typeof L==='undefined')tryAltCDN();}},msec);
  var altTried=false;
  function tryAltCDN(){{
    if(altTried){{skipMap();return;}}
    altTried=true;
    var altJs=document.createElement('script');altJs.id='leaf-js-alt';
    altJs.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    altJs.onload=function(){{clearTimeout(t);cb();}};
    altJs.onerror=skipMap;
    document.head.appendChild(altJs);
  }}
  function waitL(){{var n=0;var i=setInterval(function(){{if(typeof L!=='undefined'){{clearInterval(i);clearTimeout(t);cb();}}else if(++n>80){{clearInterval(i);skipMap();}}}},100);}}
  function skipMap(){{
    var m=document.getElementById('map');
    if(m&&!m.classList.contains('map-fallback')){{m.outerHTML='<div id="map" class="map-fallback">&#128506; Mapa no disponible sin conexion a internet<br><small>Las visualizaciones de datos funcionan offline.</small></div>';}}
  }}
}}

function renderMap(){{
  if(typeof L==='undefined'){{
    var m=document.getElementById('map');
    if(m&&m.classList.contains('map-fallback'))return;
    if(m){{m.outerHTML='<div id="map" class="map-fallback">&#128506; Leaflet no se pudo cargar<br><small>Usa los graficos y la tabla para explorar los resultados.</small></div>';}}
    return;
  }}

  var container=document.getElementById('map');
  if(!container)return;
  if(container.classList.contains('map-fallback')){{
    container.outerHTML='<div id="map" class="maplg"></div>';
    container=document.getElementById('map');
  }}
  if(mapInstance){{mapInstance.remove();mapInstance=null;}}
  container.className='maplg';
  container.innerHTML='';
  container.style.display='';

  var map=L.map('map').setView([-37.2,-72.7],8);
  mapInstance=map;
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'&copy; OpenStreetMap',maxZoom:16}}).addTo(map);

  var o=SOL.origen;
  var mulIcon=L.divIcon({{html:'<div style="background:#c62828;color:#fff;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;border:3px solid #fff;box-shadow:0 0 8px rgba(0,0,0,.5)">M</div>',iconSize:[18,18],iconAnchor:[9,9]}});
  L.marker([o.lat,o.lon],{{icon:mulIcon}}).addTo(map).bindPopup('<b>'+o.nombre+'</b><br>Planta origen');

  var deps=getFilteredData();
  var maxVol=Math.max.apply(null,SOL.despachos.map(function(d){{return d.volumen_m3;}}));
  var activeF=curProduct!=='all'||curDest!=='all';

  var destVol={{}},destProducts={{}};
  deps.forEach(function(d){{destVol[d.destino]=(destVol[d.destino]||0)+d.volumen_m3;destProducts[d.destino]=d.producto;}});

  function destIcon(color,vol,active){{var s=active?12:7;
    return L.divIcon({{html:'<div style="background:'+color+';color:#fff;border-radius:50%;width:'+s+'px;height:'+s+'px;border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,.3);opacity:'+(active?'1':'0.35')+'"></div>',iconSize:[s,s],iconAnchor:[s/2,s/2]}});
  }}

  var pc={{P1:'#1565c0',P2:'#2e7d32',P3:'#ef6c00'}};

  var DRAWN={{}};
  SOL.despachos.forEach(function(d){{
    if(d.volumen_m3<1)return;
    var key=d.destino;
    var dest=SOL.destinos[d.destino];if(!dest)return;

    var isActive=(curProduct==='all'||d.producto===curProduct)&&(curDest==='all'||d.destino===curDest);
    var w=Math.max(2,12*d.volumen_m3/maxVol);
    var c=pc[d.producto]||'#333';
    var opacity=isActive?0.85:(activeF?0.08:0.75);

    if(!DRAWN[key]){{
      DRAWN[key]=true;
      var vol=SOL.despachos.filter(function(x){{return x.destino===key&&x.volumen_m3>0;}}).reduce(function(s,x){{return s+x.volumen_m3;}},0);
      var activeDest=(curDest==='all'||curDest===key)&&(curProduct==='all'||SOL.despachos.some(function(x){{return x.destino===key&&x.producto===curProduct&&x.volumen_m3>0;}}));
      var clr=activeDest&&vol>0?'#1b5e20':'#b0b0b0';
      L.marker([dest.lat,dest.lon],{{icon:destIcon(clr,vol,activeDest&&vol>0),opacity:activeDest?1:0.4}}).addTo(map)
        .bindPopup('<b>'+dest.nombre+'</b><br>Total recibido: '+fmt(vol)+' m³');
    }}

    var ruta=SOL.rutas&&SOL.rutas[d.destino];
    if(ruta&&ruta.length>=2){{
      var latlngs=ruta.map(function(p){{return [p[1],p[0]];}});
      L.polyline(latlngs,{{color:c,weight:w,opacity:opacity,smoothFactor:1}}).addTo(map)
        .bindPopup('<b>'+d.producto+'</b> → '+dest.nombre
          +'<br>Volumen: '+fmt(d.volumen_m3)+' m³'
          +'<br>Distancia: '+d.distancia_km+' km (ruta real)'
          +'<br>Costo: $'+fmt(d.costo_clp)+' CLP'
          +(isActive?'':'<br><em>(fuera del filtro actual)</em>'));
    }}else{{
      L.polyline([[o.lat,o.lon],[dest.lat,dest.lon]],{{color:c,weight:w,opacity:opacity,dashArray:isActive?null:'8,6'}}).addTo(map)
        .bindPopup('<b>'+d.producto+'</b> → '+dest.nombre
          +'<br>Volumen: '+fmt(d.volumen_m3)+' m³'
          +'<br>Distancia: '+d.distancia_km+' km (linea recta)'
          +'<br>Costo: $'+fmt(d.costo_clp)+' CLP');
    }}
  }});

  setTimeout(function(){{map.invalidateSize();}},400);
}}

function renderSankey(){{
  var el=document.getElementById('sankey');if(!el)return;
  if(CH.sankey)CH.sankey.dispose();
  var c=echarts.init(el);
  var deps=getFilteredData();
  if(!deps.length){{
    c.setOption({{title:{{text:'Sin datos para el filtro actual',left:'center',top:'center',textStyle:{{color:'#999',fontSize:14}}}}}});
    CH.sankey=c;return;
  }}

  var aggregated={{}};
  deps.forEach(function(d){{
    if(d.volumen_m3<1)return;
    var key=d.destino+'|'+d.producto;
    if(!aggregated[key])aggregated[key]={{destino:d.destino,producto:d.producto,volumen:0}};
    aggregated[key].volumen+=d.volumen_m3;
  }});

  var destNames=[];var seenD={{}};
  Object.values(aggregated).forEach(function(a){{if(!seenD[a.destino]){{seenD[a.destino]=true;destNames.push(a.destino);}}}});

  var nodes=[SOL.origen.nombre];
  destNames.sort().forEach(function(k){{nodes.push(SOL.destinos[k].nombre);}});

  var links=[];
  Object.values(aggregated).forEach(function(a){{
    links.push({{source:nodes[0],target:SOL.destinos[a.destino].nombre,value:a.volumen,
      lineStyle:{{color:COLORS[a.producto],curveness:0.5}}}});
  }});

  c.setOption({{
    tooltip:{{trigger:'item',formatter:function(p){{return p.data.source+' → '+p.data.target+'<br/>'+fmt(p.data.value)+' m³';}}}},
    series:[{{type:'sankey',layoutIterations:32,emphasis:{{focus:'adjacency'}},
      data:nodes.map(function(n){{return {{name:n}};}}),links:links,
      label:{{fontSize:11,color:'#333'}},lineStyle:{{color:'gradient',curveness:0.5}}}}]}});
  CH.sankey=c;
}}

function renderTruckSankey(){{
  var el=document.getElementById('trucksankey');if(!el)return;
  if(CH.trucksankey)CH.trucksankey.dispose();
  var c=echarts.init(el);
  var deps=getFilteredData();
  if(!deps.length){{
    c.setOption({{title:{{text:'Sin datos para el filtro actual',left:'center',top:'center',textStyle:{{color:'#999',fontSize:14}}}}}});
    CH.trucksankey=c;return;
  }}

  var aggregated={{}};
  deps.forEach(function(d){{
    var viajes=d.camiones_viajes||0;
    if(!viajes)return;
    var key=d.destino+'|'+d.producto;
    if(!aggregated[key])aggregated[key]={{destino:d.destino,producto:d.producto,viajes:0}};
    aggregated[key].viajes+=viajes;
  }});

  var destNames=[];var seenD={{}};
  Object.values(aggregated).forEach(function(a){{if(!seenD[a.destino]){{seenD[a.destino]=true;destNames.push(a.destino);}}}});

  var nodes=[SOL.origen.nombre];
  destNames.sort().forEach(function(k){{nodes.push(SOL.destinos[k].nombre);}});

  var links=[];
  Object.values(aggregated).forEach(function(a){{
    links.push({{source:nodes[0],target:SOL.destinos[a.destino].nombre,value:a.viajes,
      lineStyle:{{color:COLORS[a.producto],curveness:0.5}}}});
  }});

  c.setOption({{
    tooltip:{{trigger:'item',formatter:function(p){{return p.data.source+' → '+p.data.target+'<br/>'+fmt(p.data.value)+' viajes/ano';}}}},
    series:[{{type:'sankey',layoutIterations:32,emphasis:{{focus:'adjacency'}},
      data:nodes.map(function(n){{return {{name:n}};}}),links:links,
      label:{{fontSize:11,color:'#333'}},lineStyle:{{color:'gradient',curveness:0.5}}}}]}});
  CH.trucksankey=c;
}}

function renderCostBar(){{
  var el=document.getElementById('costbar');if(!el)return;
  if(CH.costbar)CH.costbar.dispose();
  var c=echarts.init(el),destMap={{}};
  var deps=getFilteredData();
  deps.forEach(function(d){{var n=SOL.destinos[d.destino].nombre;if(!destMap[n])destMap[n]={{P1:0,P2:0,P3:0}};destMap[n][d.producto]+=d.costo_clp;}});
  var names=Object.keys(destMap).sort(function(a,b){{var ta=destMap[a].P1+destMap[a].P2+destMap[a].P3,tb=destMap[b].P1+destMap[b].P2+destMap[b].P3;return tb-ta;}});
  c.setOption({{
    tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}},formatter:function(p){{var s=p[0].axisValue+'<br/>',t=0;p.forEach(function(i){{s+=i.marker+i.seriesName+': $'+fmt(i.value)+'<br/>';t+=i.value;}});s+='<b>Total: $'+fmt(t)+'</b>';return s;}}}},
    legend:{{data:['P1','P2','P3'],top:0}},grid:{{left:10,right:10,top:40,bottom:0,containLabel:true}},
    xAxis:{{type:'value',axisLabel:{{formatter:function(v){{return '$'+(v/1e6).toFixed(0)+'M';}}}}}},
    yAxis:{{type:'category',data:names.length?names:[' '],axisLabel:{{fontSize:10,width:90,overflow:'truncate'}}}},
    series:['P1','P2','P3'].map(function(j){{return {{name:j,type:'bar',stack:'total',data:names.map(function(n){{return destMap[n][j]||0;}}),itemStyle:{{color:COLORS[j]}},emphasis:{{focus:'series'}}}};}})}});
  CH.costbar=c;
}}

function renderStackBar(){{
  var el=document.getElementById('stackbar');if(!el)return;
  if(CH.stackbar)CH.stackbar.dispose();
  var c=echarts.init(el),destMap={{}};
  var deps=getFilteredData();
  deps.forEach(function(d){{var n=SOL.destinos[d.destino].nombre;if(!destMap[n])destMap[n]={{P1:0,P2:0,P3:0}};destMap[n][d.producto]+=d.volumen_m3;}});
  var names=Object.keys(destMap).sort();
  if(!names.length)names=[' '];
  c.setOption({{
    tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}}}},legend:{{data:['P1','P2','P3'],top:0}},grid:{{left:10,right:10,top:40,bottom:0,containLabel:true}},
    xAxis:{{type:'category',data:names,axisLabel:{{fontSize:10,rotate:25,width:90,overflow:'truncate'}}}},yAxis:{{type:'value',name:'m³'}},
    series:['P1','P2','P3'].map(function(j){{return {{name:j,type:'bar',stack:'total',data:names.map(function(n){{return destMap[n][j]||0;}}),itemStyle:{{color:COLORS[j]}},emphasis:{{focus:'series'}},label:{{show:true,position:'inside',fontSize:10,formatter:function(p){{return p.value>200?fmt(p.value):'';}}}}}};}})}});
  CH.stackbar=c;
}}

function renderScatter(){{
  var el=document.getElementById('scatter');if(!el)return;
  if(CH.scatter)CH.scatter.dispose();
  var c=echarts.init(el);
  var deps=getFilteredData();
  var series=SOL.productos.map(function(j){{
    var pts=deps.filter(function(d){{return d.producto===j&&d.volumen_m3>0;}}).map(function(d){{return [d.distancia_km,d.volumen_m3];}});
    return {{name:j,type:'scatter',data:pts,symbolSize:function(d){{return Math.sqrt(d[1])*0.8;}},itemStyle:{{color:COLORS[j]}},emphasis:{{focus:'series'}}}};
  }});
  c.setOption({{
    tooltip:{{formatter:function(p){{return p.seriesName+'<br/>Dist: '+p.value[0]+' km<br/>Vol: '+fmt(p.value[1])+' m³';}}}},legend:{{data:['P1','P2','P3'],top:0}},grid:{{left:10,right:10,top:40,bottom:0,containLabel:true}},xAxis:{{type:'value',name:'Distancia (km)',min:0}},yAxis:{{type:'value',name:'Volumen (m³)',min:0}},series:series}});
  CH.scatter=c;
}}

function renderTable(){{
  var tbody=document.querySelector('#detailtbl tbody');if(!tbody)return;
  var deps=getFilteredData();
  var rows=deps.slice().sort(function(a,b){{return b.volumen_m3-a.volumen_m3 || a.destino.localeCompare(b.destino);}});
  if(!rows.length){{tbody.innerHTML='<tr><td colspan="9" style="text-align:center;color:var(--muted);padding:20px">Sin despachos para el filtro actual.</td></tr>';return;}}
  tbody.innerHTML=rows.map(function(d){{
    var badg='<span class="badge '+d.producto.toLowerCase()+'">'+d.producto+'</span>';
    var unit=d.volumen_m3>0?d.costo_clp/d.volumen_m3:0;
    var viajes=d.camiones_viajes||'—';
    var costCam=d.camiones_costo_total?('$'+fmt(d.camiones_costo_total)):'—';
    var costTren=d.tren_costo_estimado?('$'+fmt(d.tren_costo_estimado)):'N/A';
    return '<tr><td>'+SOL.destinos[d.destino].nombre+'</td><td>'+badg+'</td><td>'+d.distancia_km+'</td><td>'+fmt(d.volumen_m3)+'</td><td>$'+fmt(d.costo_clp)+'</td><td>$'+fmt(unit)+'</td><td>'+viajes+'</td><td>'+costCam+'</td><td>'+costTren+'</td></tr>';
  }}).join('');
}}

function renderTruckChart(){{
  var el=document.getElementById('truckchart');if(!el)return;
  if(CH.truck)CH.truck.dispose();
  var c=echarts.init(el);
  var deps=getFilteredData();
  var destViajes={{}};
  deps.forEach(function(d){{if(d.camiones_viajes)destViajes[SOL.destinos[d.destino].nombre]=(destViajes[SOL.destinos[d.destino].nombre]||0)+d.camiones_viajes;}});
  var names=Object.keys(destViajes).sort(function(a,b){{return destViajes[b]-destViajes[a];}});
  if(!names.length)names=[' '];
  c.setOption({{
    tooltip:{{trigger:'axis'}},grid:{{left:10,right:10,top:10,bottom:0,containLabel:true}},
    xAxis:{{type:'category',data:names,axisLabel:{{fontSize:10,rotate:25,width:90,overflow:'truncate'}}}},
    yAxis:{{type:'value',name:'Viajes/ano'}},
    series:[{{type:'bar',data:names.map(function(n){{return destViajes[n]||0;}}),itemStyle:{{color:'#1565c0'}},label:{{show:true,position:'top',fontSize:11}}}}]
  }});
  CH.truck=c;
}}

function renderModalChart(){{
  var el=document.getElementById('modalchart');if(!el)return;
  if(CH.modal)CH.modal.dispose();
  var c=echarts.init(el);
  var deps=getFilteredData();
  var camTotal=0,trenTotal=0;
  deps.forEach(function(d){{if(d.camiones_costo_total)camTotal+=d.camiones_costo_total;if(d.tren_costo_estimado)trenTotal+=d.tren_costo_estimado;}});
  var trenAplicable=deps.some(function(d){{return d.tren_costo_estimado;}});
  var series=[{{name:'Camion',type:'bar',data:[camTotal],itemStyle:{{color:'#1565c0'}},label:{{show:true,position:'top',fontSize:12,formatter:'$'+fmt(camTotal)}}}}];
  if(trenAplicable){{
    series.push({{name:'Tren (est.)',type:'bar',data:[trenTotal],itemStyle:{{color:'#ef6c00'}},label:{{show:true,position:'top',fontSize:12,formatter:'$'+fmt(trenTotal)}}}});
  }}
  c.setOption({{tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}},formatter:function(p){{var s='';p.forEach(function(i){{s+=i.marker+i.seriesName+': $'+fmt(i.value)+'<br/>';}});return s;}}}},
    grid:{{left:10,right:10,top:20,bottom:0,containLabel:true}},
    xAxis:{{type:'category',data:['Costo total anual']}},
    yAxis:{{type:'value',name:'CLP',axisLabel:{{formatter:function(v){{return '$'+(v/1e6).toFixed(1)+'M';}}}}}},
    series:series}});
  CH.modal=c;
}}

function refreshAll(){{
  safeCall(renderKPIs,'KPIs');
  loadLeaflet(function(){{safeCall(renderMap,'Mapa');}});
  safeCall(renderSankey,'Sankey');
  safeCall(renderTruckSankey,'TruckSankey');
  safeCall(renderCostBar,'CostBar');
  safeCall(renderStackBar,'StackBar');
  safeCall(renderScatter,'Scatter');
  safeCall(renderTable,'Tabla');
  safeCall(renderTruckChart,'TruckChart');
  safeCall(renderModalChart,'ModalChart');
}}

function renderAll(){{
  var repSel=document.getElementById('repsel');
  var repKeys=SOL.replicas?Object.keys(SOL.replicas).filter(function(k){{return k!=='avg';}}).sort():[];
  repSel.innerHTML='<option value="avg">Promedio 5 replicas</option>'+repKeys.map(function(k){{return '<option value="'+k+'">Replica '+k+'</option>';}}).join('');

  var destSel=document.getElementById('destsel');
  destSel.innerHTML='<option value="all">Todos los destinos</option>'+SOL.destinos_list.map(function(k){{return '<option value="'+k+'">'+SOL.destinos[k].nombre+'</option>';}}).join('');

  repSel.onchange=function(){{curReplica=this.value;refreshAll();}};
  document.getElementById('prodsel').onchange=function(){{curProduct=this.value;refreshAll();}};
  destSel.onchange=function(){{curDest=this.value;refreshAll();}};
  refreshAll();
}}

(function(){{
  var ld=document.getElementById('loader');ld.style.display='block';
  renderAll();
  ld.style.display='none';
  window.addEventListener('resize',function(){{Object.values(CH).forEach(function(c){{try{{c.resize();}}catch(e){{}}}});if(mapInstance)mapInstance.invalidateSize();}});
}})();
</script>
</body>
</html>'''

OUTPUT = OUT / "dashboard_distribucion.html"
OUTPUT.write_text(HTML, encoding="utf-8")
print(f"Dashboard generado: {OUTPUT}")
print(f"  Tamaño: {OUTPUT.stat().st_size / 1024:.0f} KB")
