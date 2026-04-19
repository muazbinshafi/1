document.addEventListener('DOMContentLoaded', () => {
    fetchAnalytics();
    fetchLeads();
});

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

async function fetchAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        document.getElementById('stat-total').textContent = data.total;
        document.getElementById('stat-contacted').textContent = data.contacted;
        document.getElementById('stat-pending').textContent = data.pending;
    } catch (error) {
        console.error('Error fetching analytics:', error);
    }
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
    const tbody = document.getElementById('leads-tbody');
    tbody.innerHTML = '';

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.id = `lead-${lead.id}`;

        tr.innerHTML = `
            <td>${escapeHTML(lead.name)}</td>
            <td>${escapeHTML(lead.type)}</td>
            <td>${escapeHTML(lead.city)}</td>
            <td>${escapeHTML(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp" onclick="handleWhatsAppClick(${lead.id}, '${escapeHTML(lead.name.replace(/'/g, "\\'"))}', '${escapeHTML(lead.type)}', '${escapeHTML(lead.phone)}')">
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function generateWhatsAppMessage(name, type) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 2);
    const targetDay = days[targetDate.getDay()];

    let sector = "Services";
    let entity = "Service";
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";

    if (type.toLowerCase().includes('clinic')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase().includes('retail') || type.toLowerCase().includes('store')) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    }

    const message = `Hello ${name} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${targetDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(message);
}

async function handleWhatsAppClick(id, name, type, phone) {
    // Format phone number (remove dashes/spaces, ensure it starts with 92)
    const formattedPhone = phone.replace(/[-\s]/g, '').replace(/^0/, '92');
    const message = generateWhatsAppMessage(name, type);
    const url = `https://wa.me/${formattedPhone}?text=${message}`;

    // Open WhatsApp in new tab BEFORE backend call to avoid popup blockers
    window.open(url, '_blank');

    // Optimistic UI update
    const row = document.getElementById(`lead-${id}`);
    if (row) {
        row.remove();
    }

    // Update stats optimistically
    const pendingEl = document.getElementById('stat-pending');
    const contactedEl = document.getElementById('stat-contacted');
    pendingEl.textContent = parseInt(pendingEl.textContent) - 1;
    contactedEl.textContent = parseInt(contactedEl.textContent) + 1;

    try {
        await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        });

        // Refresh analytics to ensure correctness
        fetchAnalytics();
    } catch (error) {
        console.error('Error updating lead status:', error);
        // If it fails, we should ideally fetch leads again to restore the row
        fetchLeads();
        fetchAnalytics();
    }
}
