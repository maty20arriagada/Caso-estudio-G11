const echarts=require('./echarts.min.js');const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('parte1/output/dashboard.html','utf8');
const sc=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
let syn=true;sc.forEach((c,i)=>{try{new Function(c);}catch(e){syn=false;console.log('SINTAXIS#'+(i+1)+':'+e.message);}});
const inst=[];const oi=echarts.init;echarts.init=function(){const x=oi(null,null,{ssr:true,renderer:'svg',width:760,height:420});inst.push(x);return x;};
function el(){return{innerHTML:'',style:{},dataset:{},disabled:false,classList:{contains:()=>true,toggle:()=>{}},querySelectorAll:()=>[],querySelector:()=>el(),addEventListener(){},appendChild(){},onclick:null,onchange:null};}
const ctx={echarts,console,setTimeout:()=>0,clearTimeout:()=>{},setInterval:()=>0,clearInterval:()=>{},requestAnimationFrame:()=>0,
  document:{getElementById:()=>el(),querySelector:()=>el(),querySelectorAll:()=>[],addEventListener(){}},window:{addEventListener:()=>{}}};
vm.createContext(ctx);try{vm.runInContext(sc[1],ctx);}catch(e){console.log('RUN:',e.message);process.exit(1);}
let bad=0;inst.forEach(x=>{try{if(x.renderToSVGString().length<50)bad++;}catch(e){bad++;}});
const D=JSON.parse(fs.readFileSync('parte1/output/dashboard_data.json','utf8')).meta;
console.log('Sintaxis:'+(syn?'OK':'ERR')+' charts:'+inst.length+' err:'+bad+' | warmup_days='+D.warmup_days+' (apunte='+D.warmup_apunte_days+' inter='+D.warmup_inter_days+' welch='+D.warmup_welch_days+')');
console.log((syn&&!bad)?'OK':'REVISAR');
