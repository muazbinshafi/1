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

function getChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2);
    return days[d.getDay()];
}

function getTerm(type, termType) {
    const t = type.toLowerCase();
    if (termType === 'sector') {
        if (t === 'clinic') return 'Healthcare';
        if (t === 'store') return 'Retail';
        if (t === 'service') return 'Services';
        return 'Local Business';
    }
    if (termType === 'clients') {
        if (t === 'clinic') return 'Patients';
        if (t === 'store') return 'Customers';
        if (t === 'service') return 'Clients';
        return 'Customers';
    }
    if (termType === 'action') {
        if (t === 'clinic') return 'book appointments';
        if (t === 'store') return 'browse products';
        if (t === 'service') return 'book appointments';
        return 'engage';
    }
    if (termType === 'focus') {
        if (t === 'clinic') return 'care';
        if (t === 'store') return 'sales';
        if (t === 'service') return 'services';
        return 'your work';
    }
    return type;
}

function createWhatsAppMessage(name, type) {
    const sector = getTerm(type, 'sector');
    const entity = type;
    const clients = getTerm(type, 'clients');
    const action = getTerm(type, 'action');
    const focus = getTerm(type, 'focus');
    const day = getChatDay();

    const msg = `Hello ${name} 👋,
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

    return encodeURIComponent(msg);
}

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('stat-total').textContent = data.total;
        document.getElementById('stat-new').textContent = data.new;
        document.getElementById('stat-contacted').textContent = data.contacted;
    } catch (e) {
        console.error('Error fetching stats:', e);
    }
}

async function fetchLeads() {
    try {
        const res = await fetch('/api/leads');
        const leads = await res.json();
        const tbody = document.getElementById('leads-body');
        tbody.innerHTML = '';

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.dataset.id = lead.id;

            const cleanPhone = lead.phone.replace(/[-\s]/g, '').replace(/^0/, '');
            const message = createWhatsAppMessage(lead.business_name, lead.type);
            const waLink = `https://wa.me/92${cleanPhone}?text=${message}`;

            tr.innerHTML = `
                <td>${escapeHTML(lead.business_name)}</td>
                <td>${escapeHTML(lead.type)}</td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp" data-id="${lead.id}" data-link="${waLink}">Send WhatsApp</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Error fetching leads:', e);
    }
}

document.getElementById('leads-body').addEventListener('click', async (e) => {
    if (e.target.classList.contains('btn-whatsapp')) {
        const btn = e.target;
        const id = btn.dataset.id;
        const link = btn.dataset.link;

        // Open WhatsApp synchronously to avoid popup blockers
        window.open(link, '_blank');

        // Optimistic UI update
        const row = btn.closest('tr');
        if (row) row.remove();

        // Update stats optimistically
        const statNew = document.getElementById('stat-new');
        const statContacted = document.getElementById('stat-contacted');
        if (statNew && statContacted) {
            statNew.textContent = Math.max(0, parseInt(statNew.textContent) - 1);
            statContacted.textContent = parseInt(statContacted.textContent) + 1;
        }

        // Notify backend
        try {
            await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id })
            });
            // Re-sync just in case
            fetchStats();
        } catch (err) {
            console.error('Error marking as contacted:', err);
        }
    }
});

// Initial load
fetchStats();
fetchLeads();

// Polling
setInterval(() => {
    fetchStats();
    fetchLeads();
}, 30000);
