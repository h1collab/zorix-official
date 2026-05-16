// app.js - Zorix OS 模拟器核心交互
(function(){
  const cursor = document.getElementById('cursor');
  const desktop = document.getElementById('desktop');
  const finderIcon = document.getElementById('finder-icon');
  const finderWindow = document.getElementById('finder-window');
  const finderBody = document.getElementById('finder-body');
  const fileList = document.getElementById('file-list');
  const newFileBtn = document.getElementById('new-file');
  const pushGithubBtn = document.getElementById('push-github');
  const timeEl = document.getElementById('time');

  // 光标位置（可用鼠标或键盘箭头键移动）
  let cx = window.innerWidth / 2;
  let cy = window.innerHeight / 2;
  let keyboardControl = false;

  function updateCursor(){
    cursor.style.left = cx + 'px';
    cursor.style.top = cy + 'px';
  }
  updateCursor();

  // 鼠标移动时更新光标并打开鼠标控制模式
  window.addEventListener('mousemove', (e)=>{
    cx = e.clientX; cy = e.clientY; updateCursor(); keyboardControl = false;
  });

  // 键盘箭头移动光标
  window.addEventListener('keydown', (e)=>{
    const step = e.shiftKey ? 20 : 8;
    let used = false;
    if(e.key === 'ArrowLeft'){ cx = Math.max(0, cx - step); used = true; }
    if(e.key === 'ArrowRight'){ cx = Math.min(window.innerWidth, cx + step); used = true; }
    if(e.key === 'ArrowUp'){ cy = Math.max(0, cy - step); used = true; }
    if(e.key === 'ArrowDown'){ cy = Math.min(window.innerHeight, cy + step); used = true; }
    if(used){ keyboardControl = true; updateCursor(); e.preventDefault(); }
    // Enter 模拟点击（在光标位置最接近的图标或按钮）
    if(e.key === 'Enter' && keyboardControl){ simulateClickAt(cx, cy); }
  });

  // 简单的“在坐标处找可点击元素并触发”逻辑
  function simulateClickAt(x,y){
    const el = document.elementFromPoint(x,y);
    if(!el) return;
    el.click();
  }

  // 显示时间
  function tick(){
    const d = new Date();
    const hh = String(d.getHours()).padStart(2,'0');
    const mm = String(d.getMinutes()).padStart(2,'0');
    timeEl.textContent = hh + ':' + mm;
  }
  tick(); setInterval(tick,60000);

  // 双击 Finder 图标或点击 Dock 打开窗口
  finderIcon.addEventListener('dblclick', ()=>{ openFinder(); });
  document.getElementById('dock-finder').addEventListener('click', openFinder);

  function openFinder(){
    finderWindow.style.display = 'flex';
    finderWindow.setAttribute('aria-hidden','false');
    bringToFront(finderWindow);
    refreshFileList();
  }

  // 简单拖拽窗口
  (function makeDraggable(win){
    let dragging=false, ox=0, oy=0;
    const header = win.querySelector('.window-header');
    header.addEventListener('mousedown', (e)=>{
      dragging=true; ox = e.clientX - win.offsetLeft; oy = e.clientY - win.offsetTop; win.style.transition='none';
      bringToFront(win);
    });
    window.addEventListener('mousemove',(e)=>{
      if(!dragging) return; win.style.left = (e.clientX - ox) + 'px'; win.style.top = (e.clientY - oy) + 'px';
    });
    window.addEventListener('mouseup',()=>{ dragging=false; win.style.transition='all 0.12s ease'; });
  })(finderWindow);

  function bringToFront(el){
    // 简单把 z-index 提高
    document.querySelectorAll('.window').forEach(w=>w.style.zIndex=40);
    el.style.zIndex=60;
  }

  // 本地文件列表（保存在 sessionStorage）
  function listFiles(){
    const raw = sessionStorage.getItem('zorix-files');
    return raw ? JSON.parse(raw) : [{name:'README.txt',content:'这是 Zorix 模拟器里的示例 README。\n可以用"新建文件"创建本地文件。'}];
  }
  function saveFiles(arr){ sessionStorage.setItem('zorix-files', JSON.stringify(arr)); }

  function refreshFileList(){
    const arr = listFiles();
    fileList.innerHTML='';
    arr.forEach((f,idx)=>{
      const li = document.createElement('li');
      li.innerHTML = `<span>${f.name}</span><div><button data-idx="${idx}" class="download">下载</button> <button data-idx="${idx}" class="delete">删除</button></div>`;
      fileList.appendChild(li);
    });

    fileList.querySelectorAll('.download').forEach(btn=>{
      btn.addEventListener('click', (e)=>{ const i=+btn.dataset.idx; downloadFile(listFiles()[i]); });
    });
    fileList.querySelectorAll('.delete').forEach(btn=>{
      btn.addEventListener('click', (e)=>{ const i=+btn.dataset.idx; const arr=listFiles(); arr.splice(i,1); saveFiles(arr); refreshFileList(); });
    });
  }

  function downloadFile(file){
    const blob = new Blob([file.content],{type:'text/plain;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = file.name; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  newFileBtn.addEventListener('click', ()=>{
    const name = prompt('新文件名（示例：note.txt）','note.txt');
    if(!name) return;
    const content = prompt('初始内容（可留空）','');
    const arr = listFiles(); arr.push({name,content}); saveFiles(arr); refreshFileList();
  });

  // 示例：推回 GitHub（需要用户提供个人访问令牌 PAT）
  pushGithubBtn.addEventListener('click', async ()=>{
    alert('此功能为演示：实际写入 GitHub 需要你提供一个拥有 repo 权限的个人访问令牌 (PAT)。请在弹���框输入后阅读代码或在受信环境下使用。');
    const token = prompt('请输入你的 GitHub PAT（仅用于示例，不会被本代码发送到第三方）');
    if(!token) return alert('未提供令牌，取消');
    const path = prompt('在仓库中保存的路径（例如 zorix-sim/hello.txt）','zorix-sim/hello.txt');
    if(!path) return;
    const content = prompt('文件内容','Hello from Zorix simulator');

    // 把字符串编码为 base64
    const b64 = btoa(unescape(encodeURIComponent(content)));

    // 注意：下面的请求会尝试写入仓库。如果要运行，请在具备权限且明确知道目标 repo/分支的情况下执行。
    // 示例仓库/分支： h1collab/zorix-official, branch: zorix-sim-generator
    const owner = prompt('目标仓库 owner (例如 h1collab)','h1collab');
    const repo = prompt('目标仓库名 (例如 zorix-official)','zorix-official');
    const branch = prompt('目标分支 (例如 zorix-sim-generator)','zorix-sim-generator');

    const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
    try{
      const res = await fetch(apiUrl,{
        method:'PUT',
        headers:{
          'Authorization':'token ' + token,
          'Content-Type':'application/json'
        },
        body: JSON.stringify({
          message: 'Add file from Zorix simulator',
          content: b64,
          branch: branch
        })
      });
      const data = await res.json();
      if(res.ok) alert('已写入：' + data.content.path);
      else alert('失败：' + (data.message || JSON.stringify(data)));
    }catch(err){ alert('请求失败：' + err.message); }
  });

  // 初始化文件列表
  refreshFileList();

  // 鼠标点击桌面上的图标（示例：打开 README）
  desktop.addEventListener('click',(e)=>{
    const icon = e.target.closest('.icon');
    if(!icon) return;
    const name = icon.dataset.name || icon.querySelector('.icon-label').textContent;
    if(name === 'README.txt'){ const arr=listFiles(); const f=arr.find(x=>x.name==='README.txt'); if(f) downloadFile(f); }
    if(icon.id === 'finder-icon') openFinder();
  });

})();
