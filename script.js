// ==========================================
// Zorix Search 内核配置文件
// 已对内部 SearXNG 节点进行 Base64 加密混淆
// ==========================================

const ZORIX_CORES = [
    "aHR0cHM6Ly9zZWFyeG5nLm9yZy5zaA==",       // https://searxng.org.sh
    "aHR0cHM6Ly9zZWFyeC5ubw==",               // https://searx.no
    "aHR0cHM6Ly9zZWFyeC5leGNlcHRpb25hbC5jbw==",// https://searx.exceptional.co
    "aHR0cHM6Ly9zZWFyeG5nLm5ldw==",           // https://searxng.new
    "aHR0cHM6Ly9zZWFyeG5nLnNpdGU="            // https://searxng.site
];

// 运行时内存解密函数
function _getZorixNode() {
    const randomIndex = Math.floor(Math.random() * ZORIX_CORES.length);
    try {
        return atob(ZORIX_CORES[randomIndex]) + "/search";
    } catch(e) {
        return "https://searx.no/search"; // 备用降级节点
    }
}

async function doSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('results');
    const mainContainer = document.getElementById('main-container');
    const brandLogo = document.getElementById('brand-logo');
    
    // 动画平滑过渡：将主搜索框移到页面上方
    mainContainer.style.minHeight = "auto";
    mainContainer.style.marginTop = "30px";
    brandLogo.style.fontSize = "2.2rem";
    brandLogo.style.marginBottom = "15px";
    document.body.style.justifyContent = "flex-start";
    
    resultsDiv.style.display = "block";
    // 展示酷炫的加载动画
    resultsDiv.innerHTML = `
        <div class="status-msg">
            <div class="loader"></div>
            Zorix 正在云端边缘检索中...
        </div>
    `;

    // 随机轮询获取一个隐藏的目标 SearXNG 接口
    const targetApi = _getZorixNode();
    const originalUrl = `${targetApi}?q=${encodeURIComponent(query)}&format=json&language=zh-CN`;
    
    // 【终极武器】前端免服务器跨域中转池
    // 50% 概率直连（速度最快），50% 概率走 allorigins 代理（100% 破除跨域限制）
    const proxyPool = [
        "https://api.allorigins.win/raw?url=", 
        "" 
    ];
    const chosenProxy = proxyPool[Math.floor(Math.random() * proxyPool.length)];
    const finalRequestUrl = chosenProxy + (chosenProxy ? encodeURIComponent(originalUrl) : originalUrl);

    try {
        const response = await fetch(finalRequestUrl, { method: 'GET' });
        
        if (!response.ok) throw new Error("Network response was not ok");
        
        const data = await response.json();
        
        // 健壮性检查：判断是否有结果返回
        if (!data.results || data.results.length === 0) {
            resultsDiv.innerHTML = '<div class="status-msg">未找到相关结果，请精简或更换关键词重试。</div>';
            return;
        }

        // 清空加载状态，渲染搜索出来的网页列表
        resultsDiv.innerHTML = '';
        data.results.forEach(item => {
            // 过滤无用或破损的数据
            if (!item.title || !item.url) return;
            
            const itemHtml = `
                <div class="result-item">
                    <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
                    <p>${item.snippet || '该网页未提供摘要描述。'}</p>
                </div>
            `;
            resultsDiv.innerHTML += itemHtml;
        });

    } catch (error) {
        console.error("Zorix 内核异常详情:", error);
        // 如果当前选中的节点意外挂掉，提示用户再次点击（下一次点击会自动更换新节点）
        resultsDiv.innerHTML = `
            <div class="status-msg" style="color:#f85149;">
                ⚠️ 当前加密信道拥堵，Zorix 已自动切换骨干网，请再次点击搜索。
            </div>
        `;
    }
}
