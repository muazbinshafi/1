document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchLeads();
            fetchStats();
        });
    }

    const collectBtn = document.getElementById('collect-btn');
    if (collectBtn) {
        collectBtn.addEventListener('click', triggerCollection);
    }
});

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        renderTable(leads);
    } catch (e) {
        console.error("Failed to fetch leads", e);
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        document.getElementById('total-leads').textContent = stats.total;
        document.getElementById('contacted-leads').textContent = stats.contacted;
        document.getElementById('new-leads').textContent = stats.new;
    } catch (e) {
        console.error("Failed to fetch stats", e);
    }
}

function renderTable(leads) {
    const tbody = document.querySelector('#leads-table tbody');
    tbody.innerHTML = '';

    const emptyState = document.getElementById('empty-state');

    if (leads.length === 0) {
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    } else {
        if (emptyState) emptyState.classList.add('hidden');
    }

    leads.forEach(lead => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = lead.name;
        row.appendChild(nameCell);

        const typeCell = document.createElement('td');
        typeCell.textContent = lead.type;
        row.appendChild(typeCell);

        const cityCell = document.createElement('td');
        cityCell.textContent = lead.city;
        row.appendChild(cityCell);

        const phoneCell = document.createElement('td');
        phoneCell.textContent = lead.phone;
        row.appendChild(phoneCell);

        const actionCell = document.createElement('td');
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.textContent = 'Send WhatsApp 📱';
        btn.onclick = () => handleWhatsApp(lead.id, lead.name, lead.type, lead.phone);
        actionCell.appendChild(btn);
        row.appendChild(actionCell);

        tbody.appendChild(row);
    });
}

async function triggerCollection() {
    const btn = document.getElementById('collect-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Scraping...';
    }

    try {
        const response = await fetch('/api/collect', { method: 'POST' });
        const result = await response.json();
        alert(`Collected ${result.count} new leads!`);
        fetchLeads();
        fetchStats();
    } catch (e) {
        alert('Error collecting leads');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '🔍 Scrape New Leads';
        }
    }
}

function handleWhatsApp(id, name, type, phone) {
    const message = constructMessage(name, type);
    // Remove spaces from phone for URL but keep +
    const cleanPhone = phone.replace(/\s+/g, '').replace(/-/g, '');
    const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;

    // Open in new tab
    window.open(url, '_blank');

    // Mark as contacted
    markContacted(id);
}

async function markContacted(id) {
    try {
        await fetch('/api/mark_contacted', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        // Refresh lists
        fetchLeads();
        fetchStats();
    } catch (e) {
        console.error("Failed to mark contacted", e);
    }
}

function constructMessage(businessName, type) {
    let sector, entity, clients, action, focus;

    if (type === 'Clinic') {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type === 'Store') {
        sector = 'Retail';
        entity = 'Store';
        clients = 'Customers';
        action = 'browse products';
        focus = 'sales';
    } else {
        // Service
        sector = 'Services';
        entity = 'Service Provider';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const nextDay = days[(new Date().getDay() + 1) % 7];

    return `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟
**The Digital Opportunity 📈**
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entity} currently lacks a dedicated website.
**Your 24/7 Digital Partner 🕒**
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨
**Why Business Solutions?**
✅ **Competitive Advantage:** We specialize in creating platforms that outshine your competition.
🌐 **Digital Transformation:** We can elevate your ${entity} to become a recognized 'Digital Brand.'
🛠️ **Comprehensive Service:** From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${nextDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}
