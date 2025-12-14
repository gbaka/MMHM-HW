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

  const p3 = [{x:t, y:data.p_b.map((pv,i)=>pv/(data.T_b[i]*1)), name:'rho_b (approx)'}];
  // compute rho via ideal gas on client if needed
  renderPlot('plot_rhos', p3, {title:'Плотности (прибл.)', xaxis:{title:'t, s'}, yaxis:{title:'kg/m^3'}});

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
