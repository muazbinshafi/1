document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);
});

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        renderTable(leads);
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        document.getElementById('total-leads').textContent = stats.total;
        document.getElementById('contacted-leads').textContent = stats.contacted;
        document.getElementById('new-leads').textContent = stats.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

function renderTable(leads) {
    const tableBody = document.querySelector('#leads-table tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    if (leads.length === 0) {
        document.getElementById('no-leads-message').style.display = 'block';
        return;
    } else {
        document.getElementById('no-leads-message').style.display = 'none';
    }

    leads.forEach(lead => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = lead.name;
        row.appendChild(nameCell);

        const typeCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = `badge ${lead.type.toLowerCase()}`;
        badge.textContent = lead.type;
        typeCell.appendChild(badge);
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
        btn.innerHTML = '<i class="fab fa-whatsapp"></i> Send WhatsApp';
        // Use closure to capture current lead data
        btn.onclick = () => handleWhatsAppClick(btn, lead.id, lead.name, lead.type, lead.phone);
        actionCell.appendChild(btn);
        row.appendChild(actionCell);

        tableBody.appendChild(row);
    });
}

function getNextWeekday() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 1); // Tomorrow
    return days[d.getDay()];
}

function generateMessage(name, type) {
    let sector, entity, clients, action, focus;

    // Normalize type
    const t = type.toLowerCase();

    if (t.includes('clinic') || t.includes('hospital') || t.includes('medical')) {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (t.includes('store') || t.includes('shop') || t.includes('mart')) {
        sector = 'Retail';
        entity = 'Store';
        clients = 'Customers';
        action = 'buy products';
        focus = 'sales';
    } else {
        sector = 'Service';
        entity = 'Business';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const day = getNextWeekday();

    return `Hello ${name} 👋,
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

async function handleWhatsAppClick(btn, id, name, type, phone) {
    const message = generateMessage(name, type);
    const encodedMessage = encodeURIComponent(message);

    // Clean phone number (remove spaces, ensure no + if wa.me doesn't like it, but wa.me usually likes purely numeric country code)
    // Actually wa.me expects country code without +
    let cleanPhone = phone.replace(/\D/g, '');
    // If it starts with 92, keep it. If it starts with 03, replace 0 with 92.
    if (cleanPhone.startsWith('03')) {
        cleanPhone = '92' + cleanPhone.substring(1);
    }

    const url = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

    // Open in new tab
    window.open(url, '_blank');

    // Mark as contacted in backend
    try {
        const response = await fetch(`/api/leads/${id}/contacted`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Remove row from table visually immediately for better UX
            const row = btn.closest('tr');
            row.style.transition = 'opacity 0.5s';
            row.style.opacity = '0';
            setTimeout(() => row.remove(), 500);

            // Refresh stats
            fetchStats();
        } else {
            console.error('Error updating lead status.');
        }
    } catch (error) {
        console.error('Error marking lead as contacted:', error);
    }
}
