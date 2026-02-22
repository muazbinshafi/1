document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    setInterval(fetchData, 30000); // Auto-refresh every 30s
});

function fetchData() {
    fetchLeads();
    fetchStats();
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        document.getElementById('stat-total').textContent = stats.total;
        document.getElementById('stat-contacted').textContent = stats.contacted;
        document.getElementById('stat-new').textContent = stats.new;
    } catch (e) { console.error('Error fetching stats:', e); }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        renderLeads(leads);
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

function renderLeads(leads) {
    const tbody = document.querySelector('#leads-table tbody');
    const countSpan = document.getElementById('lead-count');
    const emptyState = document.getElementById('empty-state');

    tbody.innerHTML = '';
    countSpan.textContent = leads.length;

    if (leads.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');

        // Name
        const nameTd = document.createElement('td');
        nameTd.textContent = lead.name;
        tr.appendChild(nameTd);

        // Type
        const typeTd = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = `badge ${lead.business_type.toLowerCase()}`;
        badge.textContent = lead.business_type;
        badge.style.padding = '5px 10px';
        badge.style.borderRadius = '15px';
        badge.style.fontSize = '12px';
        badge.style.color = '#fff';

        // Badge Colors
        if(lead.business_type === 'Clinic') badge.style.backgroundColor = '#e91e63'; // Pink
        else if(lead.business_type === 'Store') badge.style.backgroundColor = '#ff9800'; // Orange
        else badge.style.backgroundColor = '#2196f3'; // Blue

        typeTd.appendChild(badge);
        tr.appendChild(typeTd);

        // City
        const cityTd = document.createElement('td');
        cityTd.textContent = lead.city;
        tr.appendChild(cityTd);

        // Phone
        const phoneTd = document.createElement('td');
        phoneTd.textContent = lead.phone;
        tr.appendChild(phoneTd);

        // Action
        const actionTd = document.createElement('td');
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        btn.innerHTML = '<i class="fab fa-whatsapp"></i> Send WhatsApp';
        btn.onclick = () => sendWhatsApp(lead.id, lead.name, lead.business_type, lead.phone);
        actionTd.appendChild(btn);
        tr.appendChild(actionTd);

        tbody.appendChild(tr);
    });
}

// Simple HTML escape to prevent breaking the onclick attribute
function escapeHtml(text) {
  if (!text) return text;
  return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
}

async function sendWhatsApp(id, name, type, phone) {
    // 1. Construct Message
    const template = getMessageTemplate(name, type);
    const encodedMessage = encodeURIComponent(template);
    const cleanPhone = phone.replace(/\D/g, ''); // Remove non-digits
    const url = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

    // 2. Open WhatsApp
    window.open(url, '_blank');

    // 3. Mark as Contacted (Remove from DB/View)
    try {
        await fetch(`/api/leads/${id}/contact`, { method: 'POST' });
        // Optimistically remove row or refresh
        fetchData(); // Refresh list and stats
    } catch (error) {
        console.error('Error marking lead as contacted:', error);
    }
}

function getMessageTemplate(businessName, businessType) {
    let entity = "Business";
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";
    let sector = "Local Business";

    if (businessType === 'Clinic') {
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
        sector = "Healthcare";
    } else if (businessType === 'Store') {
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
        sector = "Retail";
    } else if (businessType === 'Service') {
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
        sector = "Service";
    }

    // Current Day
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const day = days[new Date().getDay()];

    // Note: Template literals preserve newlines
    return `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entity} currently lacks a dedicated website.

*Your 24/7 Digital Partner 🕒*
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${entity} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}
