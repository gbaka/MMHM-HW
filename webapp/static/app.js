async function getDefaultParams() {
  const r = await fetch('/api/params');
  return r.json();
}

function setStatus(msg, err=false){
  const s = document.getElementById('status');
  s.textContent = msg;
  s.style.color = err ? 'crimson' : 'black';
}

async function runSim(params){
  setStatus('Запуск симуляции...');
  const r = await fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if(!r.ok){ setStatus('Ошибка сервера', true); return null }
  const data = await r.json();
  setStatus('Готово — визуализация обновлена');
  return data;
}

// Render simple placeholder content for each plot (shown on initial load)
function renderPlaceholderPlots(){
  const ids = ['plot_pressures','plot_temps','plot_rhos','plot_G'];
  ids.forEach(id=>{
    const gd = document.getElementById(id);
    if(!gd) return;
    try{ Plotly.purge(gd); }catch(e){}
    gd.style.width = '';
    gd.style.height = '';
    const traces = [{x:[0], y:[0], showlegend:false, marker:{color:'#ddd'}}];
    const layout = {
      title: {text:'', x:0.5},
      xaxis:{visible:false},
      yaxis:{visible:false},
      annotations:[{
        text: 'Нажмите «Запустить»', showarrow:false, xref:'paper', yref:'paper', x:0.5, y:0.5,
        font:{size:18, color:'#6b7280'}
      }],
      autosize:true,
      margin:{t:20, b:20, l:20, r:20}
    };
    Plotly.newPlot(gd, traces, layout, {responsive:true});
  });
}

function plotAll(data){
  const t = data.times;
  // Helper to safely re-render a Plotly graph: purge previous state, clear inline styles,
  // and create a responsive, autosized plot. This avoids cumulative inline widths
  // being applied to the container on repeated renders.
  function renderPlot(id, traces, layout, config){
    const gd = document.getElementById(id);
    if(!gd) return;
    try{
      Plotly.purge(gd);
    }catch(e){}
    // clear any inline width/height set by Plotly previously
    gd.style.width = '';
    gd.style.height = '';
    const baseLayout = Object.assign({autosize:true, margin:{t:40}}, layout || {});
    const cfg = Object.assign({responsive:true}, config || {});
    Plotly.newPlot(gd, traces, baseLayout, cfg);
  }

  const p1 = [{x:t, y:data.p_b, name:'p_b (баллон)'}, {x:t, y:data.p_emk, name:'p_emk (ёмкость)'}];
  renderPlot('plot_pressures', p1, {title:'Давления', xaxis:{title:'t, s'}, yaxis:{title:'Па'}});

  const p2 = [{x:t, y:data.T_b, name:'T_b (баллон)'}, {x:t, y:data.T_emk, name:'T_emk (ёмкость)'}];
  renderPlot('plot_temps', p2, {title:'Температуры', xaxis:{title:'t, s'}, yaxis:{title:'K'}});

  // Prefer server-provided densities (rho_b, rho_emk); fall back to ideal-gas approx if not present
  let traces_rho = [];
  if(data.rho_b && data.rho_b.length){
    traces_rho.push({x:t, y:data.rho_b, name:'rho_b (баллон)'});
  } else if(data.p_b && data.T_b){
    traces_rho.push({x:t, y:data.p_b.map((pv,i)=>pv/(data.T_b[i]*1)), name:'rho_b (approx)'});
  }
  if(data.rho_emk && data.rho_emk.length){
    traces_rho.push({x:t, y:data.rho_emk, name:'rho_emk (ёмкость)'});
  } else if(data.p_emk && data.T_emk){
    // crude approx for emk
    traces_rho.push({x:t, y:data.p_emk.map((pv,i)=>pv/(data.T_emk[i]*1)), name:'rho_emk (approx)'});
  }
  renderPlot('plot_rhos', traces_rho, {title:'Плотности', xaxis:{title:'t, s'}, yaxis:{title:'kg/m^3'}});

  const p4 = [{x:t, y:data.G, name:'G (kg/s)', type:'scatter'}];
  renderPlot('plot_G', p4, {title:'Массовый расход', xaxis:{title:'t, s'}, yaxis:{title:'kg/s'}});
}

document.addEventListener('DOMContentLoaded', async ()=>{
  const defaults = await getDefaultParams();
  const form = document.getElementById('paramsForm');
  // fill defaults where available
  for(const el of form.elements){
    if(el.name && defaults[el.name] !== undefined){ el.value = defaults[el.name]; }
  }

  // show placeholders in plots until user runs simulation
  renderPlaceholderPlots();

  document.getElementById('runBtn').addEventListener('click', async ()=>{
    const formData = new FormData(form);
    const params = {};
    for(const [k,v] of formData.entries()){
      // keep string values for non-numeric fields like gas_model
      const el = form.elements[k];
      if(el && el.tagName === 'SELECT'){
        params[k] = v;
      } else {
        params[k] = Number(v);
      }
    }
    const data = await runSim(params);
    if(data) plotAll(data);
  });

  document.getElementById('resetBtn').addEventListener('click', ()=>{
    for(const el of form.elements){ if(el.name && defaults[el.name] !== undefined){ el.value = defaults[el.name]; } }
    setStatus('Параметры сброшены');
  });

  setStatus('Готов. Нажмите "Запустить" чтобы выполнить симуляцию');
  // Plots are simple stacked blocks now; no collapse controls.
});
