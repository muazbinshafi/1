document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Auto refresh every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchLeads();
            fetchStats();
        });
    }
});

async function fetchLeads() {
    const loading = document.getElementById('loading');
    const noData = document.getElementById('no-data');
    const tbody = document.getElementById('leads-body');

    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        if (loading) loading.style.display = 'none';
        tbody.innerHTML = '';

        if (leads.length === 0) {
            if (noData) noData.style.display = 'block';
            return;
        }

        if (noData) noData.style.display = 'none';

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            // Store lead ID on the row for potential manipulation
            tr.dataset.id = lead.id;
            tr.innerHTML = `
                <td><strong>${lead.business_name}</strong></td>
                <td><span class="badge ${lead.type.toLowerCase()}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp" onclick="sendWhatsApp(${lead.id}, '${lead.business_name.replace(/'/g, "\\'")}', '${lead.type}', '${lead.phone}')">
                        <span style="margin-right: 5px;">📲</span> Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('Error fetching leads:', error);
        if (loading) loading.textContent = 'Error loading leads.';
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        updateStat('total-leads', stats.total);
        updateStat('contacted-leads', stats.contacted);
        updateStat('new-leads', stats.new);
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

function updateStat(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function sendWhatsApp(id, name, type, phone) {
    // 1. Construct Message
    const msg = constructMessage(name, type);

    // 2. Open WhatsApp (doing this first to avoid popup blockers if async await delays it too much)
    // Clean phone number: remove spaces, ensure it has country code.
    let cleanPhone = phone.replace(/\s+/g, '').replace('+', '');
    // If number starts with 0, replace with 92.
    if (cleanPhone.startsWith('0')) {
        cleanPhone = '92' + cleanPhone.substring(1);
    }

    const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(msg)}`;
    window.open(url, '_blank');

    // 3. Mark as contacted in backend and update UI
    fetch(`/api/contacted/${id}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove row from table
                const row = document.querySelector(`tr[data-id="${id}"]`);
                if (row) {
                    row.remove();
                }
                // Check if table is empty
                const tbody = document.getElementById('leads-body');
                if (tbody.children.length === 0) {
                    const noData = document.getElementById('no-data');
                    if (noData) noData.style.display = 'block';
                }
                // Update stats
                fetchStats();
            }
        })
        .catch(console.error);
}

function constructMessage(name, type) {
    // Dynamic variables based on type
    let sector, entity, clients, action, focus;
    const lowerType = type.toLowerCase();

    if (lowerType.includes('clinic')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (lowerType.includes('store') || lowerType.includes('retail')) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    } else {
        sector = "Service Industry";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    // Get next available day or generic day? Prompt says "on [Day of the Week]"
    // Usually means today or a specific day. Let's use the current day of the week.
    const dayOfWeek = new Date().toLocaleDateString('en-US', { weekday: 'long' });

    return `Hello ${name} 👋,
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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

// Expose to window for onclick
window.sendWhatsApp = sendWhatsApp;
