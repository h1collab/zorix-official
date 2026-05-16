// Zorix Search 核心内核 - 加密节点池（外界无法直接看出是 SearXNG）
// 这里的字符串是公共 SearXNG 节点的 Base64 加密版本
const ZORIX_CORES = [
    "aHR0cHM6Ly9zZWFyeC5iZQ==",       // searx.be
    "aHR0cHM6Ly9zZWFyeG5nLnNpdGU=",   // searxng.site
    "aHR0cHM6Ly9wcml2LmF1",           // priv.au
    "aHR0cHM6Ly9zZWFyeC5wZXJ2LnN5cw==" // searx.perv.sys
];

// 动态解密函数：只有在发起搜索的千分之一秒内才在内存中还原
function _getZorixNode() {
    const rawIndex = Math.floor(Math.random() * ZORIX_CORES.length);
    return atob(ZORIX_CORES[rawIndex]) + "/search";
}

async function doSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('results');
    const mainContainer = document.getElementById('main-container');
    
    // 调整布局，让搜索框移到上方（像 Google 那样）
    mainContainer.style.minHeight = "auto";
    mainContainer.style.marginTop = "40px";
    document.body.style.justifyContent = "flex-start";
    
    resultsDiv.style.display = "block";
    resultsDiv.innerHTML = '<p class="searching">Zorix 正在全网检索中...</p>';

    // 随机抽取一个隐蔽的 SearXNG 节点进行请求
    const targetApi = _getZorixNode();
    const fullUrl = `${targetApi}?q=${encodeURIComponent(query)}&format=json&language=zh-CN`;

    try {
        const response = await fetch(fullUrl, { method: 'GET' });
        const data = await response.json();
        
        if (!data.results || data.results.length === 0) {
            resultsDiv.innerHTML = '<p class="searching">未找到相关结果，请换个关键词试试。</p>';
            return;
        }

        // 渲染搜索结果
        resultsDiv.innerHTML = '';
        data.results.forEach(item => {
            const itemHtml = `
                <div class="result-item">
                    <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
                    <p>${item.snippet || '暂无网页摘要'}</p>
                </div>
            `;
            resultsDiv.innerHTML += itemHtml;
        });

    } catch (error) {
        console.error("Zorix 内核异常:", error);
        // 如果这个节点失败了，自动重试（再点一次会自动换节点）
        resultsDiv.innerHTML = '<p class="searching" style="color:#ff4444;">当前 Zorix 节点繁忙，请重新点击搜索。</p>';
    }
}
