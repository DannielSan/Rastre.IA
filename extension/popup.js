document.addEventListener('DOMContentLoaded', async () => {
    const scanBtn = document.getElementById('scan-btn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const domainLabel = document.getElementById('target-domain');
    const errorDiv = document.getElementById('error');

    // Get current tab URL
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) return;

    try {
        const url = new URL(tab.url);
        const domain = url.hostname.replace('www.', '');
        domainLabel.textContent = `Alvo: ${domain}`;

        scanBtn.addEventListener('click', async () => {
            scanBtn.disabled = true;
            loadingDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            errorDiv.style.display = 'none';

            try {
                // Call Local API
                const response = await fetch('http://localhost:8000/api/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ domain: domain })
                });

                if (!response.ok) throw new Error('Falha na requisição API');

                const leads = await response.json();
                renderResults(leads);
            } catch (err) {
                errorDiv.textContent = `Erro: ${err.message}. O servidor está rodando?`;
                errorDiv.style.display = 'block';
            } finally {
                scanBtn.disabled = false;
                loadingDiv.style.display = 'none';
            }
        });

    } catch (e) {
        domainLabel.textContent = "Domínio Inválido";
        scanBtn.disabled = true;
    }

    function renderResults(leads) {
        if (leads.length === 0) {
            resultsDiv.innerHTML = '<div style="text-align:center">Nenhum lead encontrado.</div>';
            return;
        }

        leads.forEach(lead => {
            const div = document.createElement('div');
            div.className = 'lead-item';

            const statusClass = `status-${lead.status}`;

            div.innerHTML = `
                <div>
                    <div><strong>${lead.email}</strong></div>
                    <div style="font-size:11px;color:#888">${lead.found_at.split('T')[0]}</div>
                </div>
                <div class="status ${statusClass}">${lead.status}</div>
            `;
            resultsDiv.appendChild(div);
        });
    }
});
