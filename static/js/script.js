document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchAnalytics();

    // Poll analytics occasionally
    setInterval(fetchAnalytics, 30000);
});

function escapeHTML(str) {
    if (!str) return '';
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

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        renderLeads(leads);
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

async function fetchAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        document.getElementById('total-leads').textContent = data.total_leads;
        document.getElementById('contacted-leads').textContent = data.contacted_leads;
    } catch (error) {
        console.error('Error fetching analytics:', error);
    }
}

function getPitchTemplate(name, type) {
    const isClinic = type.toLowerCase().includes('clinic') || type.toLowerCase().includes('health');
    const isRetail = type.toLowerCase().includes('store') || type.toLowerCase().includes('retail');

    const entity = isClinic ? 'Clinic' : (isRetail ? 'Retail Store' : 'Service');
    const clients = isClinic ? 'Patients' : (isRetail ? 'Customers' : 'Clients');
    const action = isClinic ? 'book appointments' : (isRetail ? 'browse products' : 'book appointments');
    const focus = isClinic ? 'care' : (isRetail ? 'sales' : 'services');

    const d = new Date();
    d.setDate(d.getDate() + 2);
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const proposedDay = days[d.getDay()];

    const sector = isClinic ? 'Healthcare' : (isRetail ? 'Retail' : 'Services');

    return `Hello ${name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity* 📈
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entity} currently lacks a dedicated website.

*Your 24/7 Digital Partner* 🕒
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${entity} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${proposedDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function sanitizePhone(phone) {
    return phone.replace(/[-\s]/g, '').replace(/^0/, '92');
}

function renderLeads(leads) {
    const tbody = document.getElementById('leads-body');
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
                <button class="whatsapp-btn" data-id="${lead.id}" data-name="${escapeHTML(lead.name)}" data-type="${escapeHTML(lead.type)}" data-phone="${escapeHTML(lead.phone)}">
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Add event listeners to buttons
    document.querySelectorAll('.whatsapp-btn').forEach(btn => {
        btn.addEventListener('click', handleWhatsAppClick);
    });
}

async function handleWhatsAppClick(e) {
    const btn = e.currentTarget;
    const id = btn.getAttribute('data-id');
    const name = btn.getAttribute('data-name');
    const type = btn.getAttribute('data-type');
    const phone = btn.getAttribute('data-phone');

    const sanitizedPhone = sanitizePhone(phone);
    const message = encodeURIComponent(getPitchTemplate(name, type));
    const waUrl = `https://wa.me/${sanitizedPhone}?text=${message}`;

    // Optimistic UI update
    const row = document.getElementById(`lead-${id}`);
    if (row) row.remove();

    // Open WA synchronously
    window.open(waUrl, '_blank');

    // Notify backend
    try {
        await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        });
        fetchAnalytics(); // Update counts
    } catch (error) {
        console.error('Failed to mark contacted:', error);
    }
}
