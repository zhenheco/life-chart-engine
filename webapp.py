#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
life-chart-engine — 本機網頁表單 (localhost only)
用瀏覽器填出生資料，後端呼叫 chart_engine.py 算盤，前端漂亮排版。
資料只在本機處理，不對外傳送。

啟動:
  python webapp.py            # 預設 http://127.0.0.1:8765
  python webapp.py --port 9000
可用系統 Python 或 venv Python 啟動 (server 只用標準庫；算盤一律用 venv)。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "scripts", "chart_engine.py")
# venv python (Windows 路徑優先，找不到再退回 Unix 佈局)
VENV_PY = os.path.join(HERE, ".venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PY):
    VENV_PY = os.path.join(HERE, ".venv", "bin", "python")

PAGE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Life Chart — 本命盤 / 人類圖 / 紫微</title>
<style>
  :root{
    --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --line:#2a2f3a;
    --txt:#e6e8ee; --muted:#9aa3b2; --accent:#7aa2ff; --accent2:#f0a868;
    --good:#6ee7a8; --warn:#ffd166; --retro:#ff8a8a; --radius:14px;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
    font-family:-apple-system,"Segoe UI","Noto Sans TC","Microsoft JhengHei",sans-serif;
    line-height:1.55;}
  .wrap{max-width:1100px;margin:0 auto;padding:28px 18px 80px;}
  h1{font-size:24px;margin:0 0 4px;letter-spacing:.5px}
  .sub{color:var(--muted);font-size:13px;margin-bottom:22px}
  .grid-form{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
  @media(max-width:680px){.grid-form{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:18px}
  label{display:block;font-size:12px;color:var(--muted);margin:0 0 6px;letter-spacing:.4px}
  input,select{width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--txt);
    border-radius:10px;padding:10px 12px;font-size:15px;font-family:inherit}
  input:focus,select:focus{outline:none;border-color:var(--accent)}
  .row2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .field{margin-bottom:14px}
  .hint{font-size:11px;color:var(--muted);margin-top:5px}
  .actions{display:flex;gap:12px;margin-top:8px;flex-wrap:wrap}
  button{cursor:pointer;border:none;border-radius:10px;padding:12px 22px;font-size:15px;font-weight:600;
    font-family:inherit;transition:.15s}
  .primary{background:var(--accent);color:#0b1020}
  .primary:hover{filter:brightness(1.1)}
  .ghost{background:transparent;color:var(--txt);border:1px solid var(--line)}
  .ghost:hover{border-color:var(--accent)}
  .ghost[disabled]{opacity:.4;cursor:not-allowed}
  #status{margin:18px 0;font-size:14px;color:var(--muted);min-height:20px}
  .err{color:var(--retro)}
  .results{margin-top:10px;display:none}
  .sec{margin-top:22px}
  .sec h2{font-size:16px;margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line);
    display:flex;align-items:center;gap:10px}
  .tag{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:999px;
    padding:4px 12px;font-size:13px;margin:3px 4px 3px 0}
  .tag.acc{border-color:var(--accent);color:var(--accent)}
  .tag.open{color:var(--muted)}
  .chips{margin:6px 0 12px}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600;font-size:12px}
  .retro{color:var(--retro);font-weight:600}
  .kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
  .kv .item{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
  .kv .item .k{font-size:11px;color:var(--muted)}
  .kv .item .v{font-size:15px;font-weight:600;margin-top:2px}
  .palaces{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}
  .palace{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:11px 12px;font-size:12.5px}
  .palace .pname{font-weight:700;font-size:14px}
  .palace .pgz{color:var(--muted);font-size:11px;float:right}
  .palace .maj{color:var(--accent2);margin-top:6px}
  .palace .min{color:var(--txt);margin-top:2px}
  .palace .adj{color:var(--muted);margin-top:2px;font-size:11.5px}
  .palace.life{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
  .flagbadge{background:var(--accent);color:#0b1020;border-radius:6px;padding:1px 6px;font-size:10px;margin-left:4px}
  details{margin-top:18px}
  summary{cursor:pointer;color:var(--muted);font-size:13px}
  pre{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:14px;
    overflow:auto;font-size:12px;max-height:420px}
  .city-row{display:flex;gap:8px;align-items:flex-end}
  .city-row > div{flex:1}
  .note{background:rgba(255,209,102,.08);border:1px solid rgba(255,209,102,.3);border-radius:10px;
    padding:10px 12px;font-size:12.5px;color:var(--warn);margin-top:14px}
  .cmp th,.cmp td{text-align:center;white-space:nowrap}
  .cmp td:first-child,.cmp th:first-child{text-align:left;color:var(--muted)}
  .cmp .center{background:rgba(122,162,255,.12)}
  .cmp .changed{color:var(--warn);font-weight:600}
  .cmp .stable td{color:var(--good)}
</style>
</head>
<body>
<div class="wrap">
  <h1>Life Chart Engine</h1>
  <div class="sub">西洋本命盤 · 人類圖 · 紫微斗數　|　資料只在本機計算，不對外傳送</div>

  <div class="card">
    <div class="grid-form">
      <div>
        <div class="field">
          <label>姓名 NAME</label>
          <input id="name" value="範例">
        </div>
        <div class="field">
          <label>性別 GENDER</label>
          <select id="gender"><option selected>女</option><option>男</option></select>
        </div>
        <div class="row2">
          <div class="field">
            <label>出生日期 DATE</label>
            <input id="date" type="date" value="2000-01-01">
          </div>
          <div class="field">
            <label>出生時間 TIME (24h)</label>
            <input id="time" type="time" value="12:00">
          </div>
        </div>
        <div class="field">
          <label>紫微運限參考日 TARGET</label>
          <input id="target" type="date" value="2025-01-01">
        </div>
      </div>
      <div>
        <div class="field">
          <label>快速帶入城市座標（僅供參考，請自行確認）</label>
          <div class="city-row">
            <div><select id="city"></select></div>
            <button class="ghost" type="button" onclick="applyCity()">帶入</button>
          </div>
          <div class="hint">會填入經緯度與「現代」時差；歷史夏令時間請務必自行核對。</div>
        </div>
        <div class="row2">
          <div class="field">
            <label>緯度 LAT</label>
            <input id="lat" type="number" step="0.0001" value="25.0330">
          </div>
          <div class="field">
            <label>經度 LON</label>
            <input id="lon" type="number" step="0.0001" value="121.5654">
          </div>
        </div>
        <div class="field">
          <label>UTC 時差 TZ（出生當時，含夏令時）</label>
          <input id="tz" type="number" step="0.5" value="8">
          <div class="hint">台灣 1980 年後＝8；1945–1979 部分年份有夏令時間需 +9。</div>
        </div>
      </div>
    </div>
    <div class="actions">
      <button class="primary" onclick="run()">算盤</button>
      <button class="ghost" onclick="compareBoundary()">邊界對照 ±30分</button>
      <button class="ghost" id="dlBtn" onclick="downloadJSON()" disabled>下載 JSON</button>
      <button class="ghost" onclick="downloadMD()">下載 Markdown</button>
      <button class="ghost" onclick="downloadPDF()">下載 PDF</button>
    </div>
  </div>

  <div id="status"></div>
  <div class="results" id="results"></div>
</div>

<script>
const CITIES = [
  ["—— 選擇城市 ——", null, null, null],
  ["台北 Taipei", 25.0330, 121.5654, 8],
  ["台中 Taichung", 24.1477, 120.6736, 8],
  ["彰化 Changhua", 24.0838, 120.4046, 8],
  ["台南 Tainan", 22.9999, 120.2270, 8],
  ["高雄 Kaohsiung", 22.6273, 120.3014, 8],
  ["花蓮 Hualien", 23.9871, 121.6015, 8],
  ["香港 Hong Kong", 22.3193, 114.1694, 8],
  ["北京 Beijing", 39.9042, 116.4074, 8],
  ["上海 Shanghai", 31.2304, 121.4737, 8],
  ["東京 Tokyo", 35.6762, 139.6503, 9],
  ["新加坡 Singapore", 1.3521, 103.8198, 8],
  ["洛杉磯 Los Angeles", 34.0522, -118.2437, -8],
  ["紐約 New York", 40.7128, -74.0060, -5],
  ["倫敦 London", 51.5074, -0.1278, 0],
];
const citySel = document.getElementById('city');
CITIES.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c[0];citySel.appendChild(o);});
function applyCity(){
  const c = CITIES[+citySel.value];
  if(!c || c[1]===null) return;
  document.getElementById('lat').value = c[1];
  document.getElementById('lon').value = c[2];
  document.getElementById('tz').value  = c[3];
}

let lastJSON = null;
const $ = id => document.getElementById(id);

async function run(){
  const body = {
    name:$('name').value, gender:$('gender').value,
    date:$('date').value, time:$('time').value,
    tz:$('tz').value, lat:$('lat').value, lon:$('lon').value,
    target:$('target').value
  };
  const st = $('status'); st.className=''; st.textContent='計算中…';
  $('results').style.display='none'; $('dlBtn').disabled=true;
  try{
    const r = await fetch('/api/chart', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data = await r.json();
    if(!data.ok){ st.className='err'; st.textContent='錯誤：'+(data.error||'未知'); return; }
    lastJSON = data;
    st.textContent='';
    render(data);
    $('dlBtn').disabled=false;
  }catch(e){ st.className='err'; st.textContent='請求失敗：'+e.message; }
}

function el(tag, cls, html){const e=document.createElement(tag); if(cls)e.className=cls; if(html!=null)e.innerHTML=html; return e;}

function render(d){
  const R = $('results'); R.innerHTML=''; R.style.display='block';
  const inp = d.input;
  R.appendChild(el('div','sub', `${inp.name}　${inp.gender}　${inp.date} ${inp.time}　UTC${inp.tz_offset>=0?'+':''}${inp.tz_offset}　(${inp.lat}, ${inp.lon})　流年參考 ${inp.target}`));

  // ---- Western ----
  const w = d.western;
  let s = el('div','sec');
  s.appendChild(el('h2',null,'西洋本命盤 <span class="tag">'+w.system+'</span>'));
  let kv = el('div','kv');
  kv.appendChild(kvItem('上升 ASC', w.ascendant.label));
  kv.appendChild(kvItem('天頂 MC', w.midheaven.label));
  s.appendChild(kv);
  let t = el('table'); t.innerHTML='<tr><th>行星</th><th>星座度數</th><th>宮位</th><th>逆行</th></tr>';
  w.planets.forEach(p=>{
    const tr=el('tr');
    tr.innerHTML=`<td>${p.name}</td><td>${p.label}</td><td>${p.house}</td>`+
      `<td class="${p.retrograde?'retro':''}">${p.retrograde?'℞ 逆':''}</td>`;
    t.appendChild(tr);
  });
  s.appendChild(t);
  const asp = w.aspects.slice(0,12).map(a=>`${a.a}–${a.b} ${a.type}(${a.orb}°)`).join('　');
  s.appendChild(el('div','hint','主要相位：'+asp));
  R.appendChild(s);

  // ---- Human Design ----
  const h = d.human_design;
  s = el('div','sec'); s.appendChild(el('h2',null,'人類圖 Human Design'));
  kv = el('div','kv');
  kv.appendChild(kvItem('類型', h.type));
  kv.appendChild(kvItem('內在權威', h.authority));
  kv.appendChild(kvItem('人生角色', h.profile));
  kv.appendChild(kvItem('定義', h.definition));
  s.appendChild(kv);
  s.appendChild(el('div','hint','輪迴交叉：'+h.incarnation_cross+'　|　設計日：'+h.design_date));
  let chips = el('div','chips');
  h.defined_centers.forEach(c=>chips.appendChild(el('span','tag acc',c)));
  h.open_centers.forEach(c=>chips.appendChild(el('span','tag open',c)));
  s.appendChild(el('div','hint','中心（亮色＝有定義）：'));
  s.appendChild(chips);
  let ch = el('div','chips');
  h.channels.forEach(c=>ch.appendChild(el('span','tag',c)));
  s.appendChild(el('div','hint','通道：'));
  s.appendChild(ch);
  let gt = el('table'); gt.innerHTML='<tr><th>行星</th><th>個性 (體)</th><th>設計</th></tr>';
  h.gates.forEach(g=>{
    gt.appendChild(el('tr',null,
      `<td>${g.planet}</td><td>${g.personality.gate}.${g.personality.line}</td><td>${g.design.gate}.${g.design.line}</td>`));
  });
  s.appendChild(gt);
  R.appendChild(s);

  // ---- Ziwei ----
  const z = d.ziwei;
  s = el('div','sec'); s.appendChild(el('h2',null,'紫微斗數'));
  kv = el('div','kv');
  kv.appendChild(kvItem('五行局', z.five_elements_class));
  kv.appendChild(kvItem('命主', z.soul));
  kv.appendChild(kvItem('身主', z.body));
  kv.appendChild(kvItem('時辰 index', String(z.hour_index)));
  s.appendChild(kv);
  let pg = el('div','palaces');
  z.palaces.forEach(p=>{
    const isLife = p.flags && p.flags.indexOf('命')>=0;
    const pc = el('div','palace'+(isLife?' life':''));
    let flag = '';
    if(p.flags && p.flags.indexOf('命')>=0) flag += '<span class="flagbadge">命</span>';
    if(p.flags && p.flags.indexOf('身')>=0) flag += '<span class="flagbadge">身</span>';
    pc.innerHTML =
      `<span class="pgz">${p.ganzhi}</span><span class="pname">${p.name}${flag}</span>`+
      (p.major_stars.length?`<div class="maj">${p.major_stars.join('　')}</div>`:`<div class="maj" style="opacity:.5">（空宮）</div>`)+
      (p.minor_stars.length?`<div class="min">${p.minor_stars.join('　')}</div>`:``)+
      (p.adjective_stars.length?`<div class="adj">${p.adjective_stars.join('　')}</div>`:``)+
      `<div class="adj">大限 ${p.decadal_range}</div>`;
    pg.appendChild(pc);
  });
  s.appendChild(pg);
  R.appendChild(s);

  // raw
  const det = el('details');
  det.appendChild(el('summary',null,'查看原始 JSON'));
  det.appendChild(el('pre',null, esc(JSON.stringify(d,null,2))));
  R.appendChild(det);
}
function kvItem(k,v){return el('div','item',`<div class="k">${k}</div><div class="v">${v}</div>`);}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

// ---- 邊界對照 ----
function curBody(timeStr){
  return {
    name:$('name').value, gender:$('gender').value,
    date:$('date').value, time:timeStr,
    tz:$('tz').value, lat:$('lat').value, lon:$('lon').value,
    target:$('target').value
  };
}
function shiftTime(hhmm, mins){
  let parts=hhmm.split(':').map(Number);
  let tot=(parts[0]*60+parts[1]+mins+1440)%1440;
  return String(Math.floor(tot/60)).padStart(2,'0')+':'+String(tot%60).padStart(2,'0');
}
async function chartAt(timeStr){
  const r=await fetch('/api/chart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(curBody(timeStr))});
  return r.json();
}
function palaceMaj(d,nm){
  const p=d.ziwei.palaces.find(x=>x.name===nm);
  return p && p.major_stars.length ? p.major_stars.join(' ') : '（空宮）';
}
async function compareBoundary(){
  const base=$('time').value;
  const offsets=[-30,-15,0,15,30];
  const times=offsets.map(o=>shiftTime(base,o));
  const st=$('status'); st.className=''; st.textContent='邊界對照計算中…（5 張盤）';
  $('results').style.display='none'; $('dlBtn').disabled=true;
  try{
    const datas=[];
    for(const t of times){ datas.push(await chartAt(t)); }
    const bad=datas.find(d=>!d.ok);
    if(bad){ st.className='err'; st.textContent='錯誤：'+(bad.error||'未知'); return; }
    st.textContent='';
    renderCompare(offsets,times,datas);
  }catch(e){ st.className='err'; st.textContent='請求失敗：'+e.message; }
}
function renderCompare(offsets,times,datas){
  const R=$('results'); R.innerHTML=''; R.style.display='block';
  const inp=datas[2].input;
  R.appendChild(el('div','sub',`邊界對照　${inp.name}　${inp.date}　以 ${times[2]} 為中心，±30 分鐘`));
  const fields=[
    ['上升 ASC', d=>d.western.ascendant.label],
    ['天頂 MC', d=>d.western.midheaven.label],
    ['HD 人生角色', d=>d.human_design.profile],
    ['HD 太陽爻 個性', d=>d.human_design.gates[0].personality.gate+'.'+d.human_design.gates[0].personality.line],
    ['HD 太陽爻 設計', d=>d.human_design.gates[0].design.gate+'.'+d.human_design.gates[0].design.line],
    ['紫微 時辰 index', d=>String(d.ziwei.hour_index)],
    ['紫微 命宮主星', d=>palaceMaj(d,'命宮')],
    ['五行局', d=>d.ziwei.five_elements_class],
    ['命主', d=>d.ziwei.soul],
    ['身主', d=>d.ziwei.body],
  ];
  const t=el('table','cmp');
  let head='<tr><th>欄位 \\ 時間</th>';
  offsets.forEach((o,i)=>{ const lbl=times[i]+(o===0?' ●':(o>0?' +'+o:' '+o)); head+=`<th class="${o===0?'center':''}">${lbl}</th>`; });
  head+='</tr>'; t.innerHTML=head;
  fields.forEach(f=>{
    const vals=datas.map(f[1]);
    const center=vals[2];
    const changed=vals.some(v=>v!==center);
    const tr=el('tr', changed?'':'stable');
    let row=`<td>${f[0]}</td>`;
    vals.forEach((v,i)=>{
      const isC=offsets[i]===0;
      const diff=v!==center;
      row+=`<td class="${isC?'center ':''}${diff?'changed':''}">${v}</td>`;
    });
    tr.innerHTML=row; t.appendChild(tr);
  });
  R.appendChild(t);
  R.appendChild(el('div','note','綠色列＝這 ±30 分鐘內完全不變（可信任）；黃色＝會隨時間變動，代表該欄位對出生時間敏感，請先確認時間精確度再採用。'));
}

function downloadJSON(){
  if(!lastJSON) return;
  saveBlob(new Blob([JSON.stringify(lastJSON,null,2)],{type:'application/json'}), 'json');
}
function fname(ext){
  const nm=($('name').value||'chart').replace(/[\\/:*?"<>|]/g,'_');
  return nm+'_'+$('date').value+'.'+ext;
}
function saveBlob(blob, ext){
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download=fname(ext); a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href), 1000);
}
function curBody2(){
  return JSON.stringify({
    name:$('name').value, gender:$('gender').value, date:$('date').value, time:$('time').value,
    tz:$('tz').value, lat:$('lat').value, lon:$('lon').value, target:$('target').value });
}
async function downloadFile(api, ext, label){
  const st=$('status'); st.className=''; st.textContent='產生 '+label+'…';
  try{
    const r=await fetch(api,{method:'POST',headers:{'Content-Type':'application/json'},body:curBody2()});
    if(!r.ok){ let msg='HTTP '+r.status; try{const j=await r.json(); msg=j.error||msg;}catch(e){} st.className='err'; st.textContent=label+' 失敗：'+msg; return; }
    const blob=await r.blob();
    saveBlob(blob, ext);
    st.textContent=label+' 已下載 ✓';
  }catch(e){ st.className='err'; st.textContent=label+' 失敗：'+e.message; }
}
function downloadMD(){ downloadFile('/api/markdown','md','Markdown'); }
function downloadPDF(){ downloadFile('/api/pdf','pdf','PDF'); }
</script>
</body>
</html>
"""


def compute(params):
    """呼叫 chart_engine.py --json，回傳解析後的 dict。"""
    args = [VENV_PY, ENGINE, "--json",
            "--name", str(params.get("name", "")),
            "--gender", str(params.get("gender", "男")),
            "--date", str(params.get("date", "")),
            "--time", str(params.get("time", "")),
            "--tz", str(params.get("tz", "8")),
            "--lat", str(params.get("lat", "")),
            "--lon", str(params.get("lon", "")),
            "--target", str(params.get("target", ""))]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    p = subprocess.run(args, capture_output=True, env=env)
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    if p.returncode != 0:
        return {"ok": False, "error": (err or out or "engine failed").strip()[:600]}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": "無法解析引擎輸出：" + out[:400]}


def compute_md(params):
    """呼叫引擎（不加 --json）取得人類可讀 Markdown 報告。"""
    args = [VENV_PY, ENGINE,
            "--name", str(params.get("name", "")),
            "--gender", str(params.get("gender", "男")),
            "--date", str(params.get("date", "")),
            "--time", str(params.get("time", "")),
            "--tz", str(params.get("tz", "8")),
            "--lat", str(params.get("lat", "")),
            "--lon", str(params.get("lon", "")),
            "--target", str(params.get("target", ""))]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    p = subprocess.run(args, capture_output=True, env=env)
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode != 0:
        return None, (p.stderr.decode("utf-8", "replace") or out or "engine failed").strip()[:600]
    return out, None


def _e(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_report_html(d):
    """從盤面 JSON 產生適合列印的 HTML 報告（淺色、紙張風）。"""
    inp = d["input"]
    w, h, z = d["western"], d["human_design"], d["ziwei"]
    prows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td class='r'>%s</td></tr>" % (
            _e(p["name"]), _e(p["label"]), p["house"], "℞" if p["retrograde"] else "")
        for p in w["planets"])
    asp = "　".join("%s–%s %s(%s°)" % (_e(a["a"]), _e(a["b"]), _e(a["type"]), a["orb"])
                    for a in w["aspects"][:14])
    cdef = "".join("<span class='tag on'>%s</span>" % _e(c) for c in h["defined_centers"])
    copen = "".join("<span class='tag'>%s</span>" % _e(c) for c in h["open_centers"])
    chans = "".join("<span class='tag'>%s</span>" % _e(c) for c in h["channels"])
    grows = "".join(
        "<tr><td>%s</td><td>%s.%s</td><td>%s.%s</td></tr>" % (
            _e(g["planet"]), g["personality"]["gate"], g["personality"]["line"],
            g["design"]["gate"], g["design"]["line"])
        for g in h["gates"])
    zrows = ""
    for p in z["palaces"]:
        maj = "　".join(_e(s) for s in p["major_stars"]) or "（空宮）"
        mino = "　".join(_e(s) for s in p["minor_stars"])
        adj = "　".join(_e(s) for s in p["adjective_stars"])
        life = " life" if (p["flags"] and "命" in p["flags"]) else ""
        zrows += "<tr class='%s'><td>%s%s</td><td>%s</td><td class='maj'>%s</td><td>%s</td><td class='adj'>%s</td><td>%s</td></tr>" % (
            life.strip(), _e(p["name"]), (" [" + _e(p["flags"]) + "]") if p["flags"] else "",
            _e(p["ganzhi"]), maj, mino, adj, _e(p["decadal_range"]))
    tzs = "+%s" % inp["tz_offset"] if inp["tz_offset"] >= 0 else str(inp["tz_offset"])
    css = """
    @page{size:A4;margin:14mm}
    *{box-sizing:border-box}
    body{font-family:"Noto Sans TC","Microsoft JhengHei","PMingLiU",sans-serif;color:#1a1a1a;font-size:12px;line-height:1.5;margin:0}
    h1{font-size:20px;margin:0 0 2px}
    .meta{color:#666;font-size:11px;margin-bottom:14px}
    h2{font-size:14px;border-bottom:2px solid #333;padding-bottom:4px;margin:18px 0 8px}
    table{width:100%;border-collapse:collapse;margin:6px 0}
    th,td{border-bottom:1px solid #ddd;padding:4px 7px;text-align:left;vertical-align:top}
    th{background:#f3f3f3;font-size:10.5px;color:#555}
    td.r{color:#c0392b;font-weight:bold}
    td.maj{color:#b9770e;font-weight:bold}
    td.adj{color:#777;font-size:10.5px}
    tr.life td{background:#eef3ff}
    .kv{margin:6px 0}
    .kv b{display:inline-block;min-width:88px;color:#555;font-weight:600}
    .tag{display:inline-block;border:1px solid #ccc;border-radius:10px;padding:1px 9px;margin:2px 3px 2px 0;font-size:11px;color:#777}
    .tag.on{border-color:#2a6;color:#176;font-weight:600}
    .hint{color:#666;font-size:11px;margin:4px 0}
    .sec{page-break-inside:avoid}
    """
    return (
        "<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
        "<title>%s Life Chart</title><style>%s</style></head><body>"
        "<h1>%s　Life Chart</h1>"
        "<div class='meta'>%s｜%s %s｜UTC%s（含夏令時）｜(%s, %s)｜紫微運限參考 %s</div>"
        "<div class='sec'><h2>西洋本命盤　%s</h2>"
        "<div class='kv'><b>上升 ASC</b>%s　　<b style='min-width:auto'>天頂 MC</b> %s</div>"
        "<table><tr><th>行星</th><th>星座度數</th><th>宮</th><th>逆</th></tr>%s</table>"
        "<div class='hint'>主要相位：%s</div></div>"
        "<div class='sec'><h2>人類圖 Human Design</h2>"
        "<div class='kv'><b>類型</b>%s　<b style='min-width:auto'>權威</b> %s　<b style='min-width:auto'>角色</b> %s　<b style='min-width:auto'>定義</b> %s</div>"
        "<div class='kv'><b>輪迴交叉</b>%s</div><div class='kv'><b>設計日</b>%s</div>"
        "<div class='hint'>中心（綠＝有定義）：</div><div>%s%s</div>"
        "<div class='hint'>通道：</div><div>%s</div>"
        "<table><tr><th>行星</th><th>個性</th><th>設計</th></tr>%s</table></div>"
        "<div class='sec'><h2>紫微斗數</h2>"
        "<div class='kv'><b>五行局</b>%s　<b style='min-width:auto'>命主</b> %s　<b style='min-width:auto'>身主</b> %s　<b style='min-width:auto'>時辰index</b> %s</div>"
        "<table><tr><th>宮位</th><th>干支</th><th>主星</th><th>輔星</th><th>雜曜</th><th>大限</th></tr>%s</table></div>"
        "<div class='meta' style='margin-top:16px'>由 life-chart-engine 計算（%s）。盤面數值由引擎實算。</div>"
        "</body></html>"
    ) % (
        _e(inp["name"]), css, _e(inp["name"]),
        _e(inp["gender"]), _e(inp["date"]), _e(inp["time"]), tzs, inp["lat"], inp["lon"], _e(inp["target"]),
        _e(w["system"]), _e(w["ascendant"]["label"]), _e(w["midheaven"]["label"]), prows, asp,
        _e(h["type"]), _e(h["authority"]), _e(h["profile"]), _e(h["definition"]),
        _e(h["incarnation_cross"]), _e(h["design_date"]), cdef, copen, chans, grows,
        _e(z["five_elements_class"]), _e(z["soul"]), _e(z["body"]), z["hour_index"], zrows,
        _e(d.get("meta", {}).get("ephemeris", "")),
    )


def find_browser():
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pfx = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    for c in (os.path.join(pf, r"Microsoft\Edge\Application\msedge.exe"),
              os.path.join(pfx, r"Microsoft\Edge\Application\msedge.exe"),
              os.path.join(pf, r"Google\Chrome\Application\chrome.exe"),
              os.path.join(pfx, r"Google\Chrome\Application\chrome.exe")):
        if os.path.exists(c):
            return c
    return None


def compute_pdf(params):
    """JSON → HTML → 用無頭 Edge/Chrome 列印成 PDF，回傳 (bytes, error)。"""
    d = compute(params)
    if not d.get("ok"):
        return None, d.get("error", "engine failed")
    browser = find_browser()
    if not browser:
        return None, "找不到 Edge 或 Chrome，無法產生 PDF"
    tmp = tempfile.mkdtemp(prefix="lifechart_")
    try:
        html_p = os.path.join(tmp, "report.html")
        pdf_p = os.path.join(tmp, "report.pdf")
        with open(html_p, "w", encoding="utf-8") as f:
            f.write(render_report_html(d))
        url = "file:///" + html_p.replace("\\", "/")
        args = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--user-data-dir=" + os.path.join(tmp, "ud"),
                "--print-to-pdf=" + pdf_p, url]
        r = subprocess.run(args, capture_output=True, timeout=90)
        if not os.path.exists(pdf_p):
            return None, "PDF 產生失敗：" + r.stderr.decode("utf-8", "replace")[:400]
        with open(pdf_p, "rb") as f:
            return f.read(), None
    except subprocess.TimeoutExpired:
        return None, "PDF 產生逾時"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 安靜
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urlparse(self.path).path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, json.dumps({"ok": False, "error": "not found"}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/chart", "/api/markdown", "/api/pdf"):
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            params = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError) as e:
            self._send(400, json.dumps({"ok": False, "error": "bad request: %s" % e}))
            return
        if path == "/api/chart":
            self._send(200, json.dumps(compute(params), ensure_ascii=False))
        elif path == "/api/markdown":
            md, err = compute_md(params)
            if err:
                self._send(500, json.dumps({"ok": False, "error": err}))
            else:
                self._send(200, md, "text/markdown; charset=utf-8")
        elif path == "/api/pdf":
            pdf, err = compute_pdf(params)
            if err:
                self._send(500, json.dumps({"ok": False, "error": err}))
            else:
                self._send(200, pdf, "application/pdf")


def main():
    port = 8765
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    if not os.path.exists(VENV_PY):
        print("error: 找不到 venv python:", VENV_PY)
        print("請先跑 setup（venv + 依賴）。")
        sys.exit(1)
    url = "http://127.0.0.1:%d/" % port
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Life Chart 網頁已啟動：", url)
    print("（只在本機 127.0.0.1 監聽；Ctrl+C 結束）")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n結束。")
        srv.shutdown()


if __name__ == "__main__":
    main()
