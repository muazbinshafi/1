document.addEventListener('DOMContentLoaded', () => {
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

function sanitizePhone(phone) {
    // Remove hyphens and spaces, then remove a leading zero if present
    // avoiding greedy character classes like [-\s^0]
    return phone.replace(/[-\s]/g, '').replace(/^0/, '');
}

function getChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2); // Calculate two days from now
    return days[d.getDay()];
}

function generateMessage(businessName, type) {
    const chatDay = getChatDay();
    let sector = 'business';
    let entity = type;
    let clients = 'Customers';
    let action = 'buy products';
    let focus = 'sales';

    if (type === 'Clinic') {
        sector = 'Healthcare';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type === 'Store') {
        sector = 'Retail';
        clients = 'Customers';
        action = 'browse products';
        focus = 'sales';
    } else if (type === 'Service') {
        sector = 'Services';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const template = `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I'm reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entity} currently lacks a dedicated website.

*Your 24/7 Digital Partner 🕒*
In today's digital world, a website acts as your most reliable assistant—it's available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${entity} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(template);
}

function fetchLeads() {
    fetch('/api/leads')
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-leads').textContent = data.analytics.total_leads || 0;
            document.getElementById('contacted-leads').textContent = data.analytics.contacted_leads || 0;

            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = '';

            data.leads.forEach(lead => {
                const tr = document.createElement('tr');
                tr.dataset.id = lead.id;

                tr.innerHTML = `
                    <td>${escapeHTML(lead.business_name)}</td>
                    <td>${escapeHTML(lead.type)}</td>
                    <td>${escapeHTML(lead.city)}</td>
                    <td>${escapeHTML(lead.phone)}</td>
                    <td>
                        <button class="btn-whatsapp" data-id="${lead.id}" data-phone="${escapeHTML(lead.phone)}" data-name="${escapeHTML(lead.business_name)}" data-type="${escapeHTML(lead.type)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
}

// Event delegation for WhatsApp buttons
document.getElementById('leads-body').addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-whatsapp')) {
        const btn = e.target;
        const id = btn.dataset.id;
        const rawPhone = btn.dataset.phone;
        const name = btn.dataset.name;
        const type = btn.dataset.type;

        // Optimistic UI update: remove row immediately
        const row = btn.closest('tr');
        if (row) row.remove();

        // Update analytics optimistically
        const contactedEl = document.getElementById('contacted-leads');
        contactedEl.textContent = parseInt(contactedEl.textContent) + 1;

        const phone = '92' + sanitizePhone(rawPhone);
        const msg = generateMessage(name, type);
        const waUrl = `https://wa.me/${phone}?text=${msg}`;

        // Open WhatsApp synchronously to avoid popup blockers
        window.open(waUrl, '_blank');

        // Notify backend
        fetch('/api/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        }).catch(err => console.error('Error updating lead:', err));
    }
});