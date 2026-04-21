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

function fetchAnalytics() {
    fetch('/api/analytics')
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-leads').textContent = data.total;
            document.getElementById('contacted-leads').textContent = data.contacted;
            document.getElementById('pending-leads').textContent = data.pending;
        });
}

function fetchLeads() {
    fetch('/api/leads')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = '';
            data.leads.forEach(lead => {
                const tr = document.createElement('tr');
                tr.dataset.id = lead.id;
                tr.innerHTML = `
                    <td>${escapeHTML(lead.name)}</td>
                    <td>${escapeHTML(lead.type)}</td>
                    <td>${escapeHTML(lead.city)}</td>
                    <td>${escapeHTML(lead.phone)}</td>
                    <td>
                        <button class="btn-whatsapp" onclick="sendWhatsApp(this, ${lead.id}, '${escapeHTML(lead.name)}', '${escapeHTML(lead.type)}', '${escapeHTML(lead.phone)}')">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
}

function formatPhoneNumber(phone) {
    return phone.replace(/[-\s]/g, '').replace(/^0/, '92');
}

function generateMessage(name, type) {
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
        action = 'buy products';
        focus = 'sales';
    } else {
        sector = 'Service';
        entity = 'Service';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const today = new Date();
    today.setDate(today.getDate() + 2);
    const dayOfWeek = today.toLocaleDateString('en-US', { weekday: 'long' });

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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function sendWhatsApp(btn, id, name, type, phone) {
    const formattedPhone = formatPhoneNumber(phone);
    const message = generateMessage(name, type);
    const url = `https://wa.me/${formattedPhone}?text=${encodeURIComponent(message)}`;

    // Open WhatsApp synchronously to avoid popup blockers
    window.open(url, '_blank');

    // Optimistic UI update
    const tr = btn.closest('tr');
    tr.style.display = 'none';

    // Update backend
    fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
    }).then(() => {
        fetchAnalytics(); // Refresh analytics
    }).catch(err => {
        console.error('Error updating status:', err);
        tr.style.display = ''; // Revert UI if error
    });
}
