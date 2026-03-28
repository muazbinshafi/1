function escapeHTML(str) {
    if (typeof str !== 'string') return str;
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

function generateWhatsAppMessage(lead) {
    const name = lead.business_name;
    const type = lead.type;

    let sector, entity, clients, action, focus;

    if (type.toLowerCase().includes('clinic') || type.toLowerCase().includes('medical')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase().includes('store') || type.toLowerCase().includes('retail') || type.toLowerCase().includes('shop')) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const day = getChatDay();

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(message);
}

function fetchStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-stat').textContent = data.total;
            document.getElementById('contacted-stat').textContent = data.contacted;
            document.getElementById('new-stat').textContent = data.new;
        })
        .catch(err => console.error('Error fetching stats:', err));
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

                const safeName = escapeHTML(lead.business_name);
                const safeType = escapeHTML(lead.type);
                const safeCity = escapeHTML(lead.city);
                const safePhone = escapeHTML(lead.phone);

                // Remove non-numeric characters for wa.me URL
                const rawPhone = lead.phone.replace(/[^0-9+]/g, '');
                const cleanPhone = rawPhone.startsWith('0') ? '92' + rawPhone.slice(1) : rawPhone.replace('+', '');

                tr.innerHTML = `
                    <td>${safeName}</td>
                    <td>${safeType}</td>
                    <td>${safeCity}</td>
                    <td>${safePhone}</td>
                    <td>
                        <button class="whatsapp-btn" data-id="${lead.id}" data-phone="${cleanPhone}">
                            Send WhatsApp
                        </button>
                    </td>
                `;

                // Attach raw lead data for dynamic msg generation
                const btn = tr.querySelector('.whatsapp-btn');
                btn.leadData = lead;

                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error('Error fetching leads:', err));
}

function handleWhatsAppClick(e) {
    if (e.target && e.target.classList.contains('whatsapp-btn')) {
        const btn = e.target;
        const id = btn.getAttribute('data-id');
        const phone = btn.getAttribute('data-phone');
        const leadData = btn.leadData;

        const text = generateWhatsAppMessage(leadData);
        const url = `https://wa.me/${phone}?text=${text}`;

        // Open synchronously to avoid popup blocker
        window.open(url, '_blank');

        // Optimistic UI update: Remove row
        const row = btn.closest('tr');
        if (row) row.remove();

        // Optimistically update counts
        const newStat = document.getElementById('new-stat');
        const contStat = document.getElementById('contacted-stat');
        newStat.textContent = parseInt(newStat.textContent) - 1;
        contStat.textContent = parseInt(contStat.textContent) + 1;

        // Call backend to update status
        fetch('/api/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status !== 'success') {
                console.error("Failed to mark as contacted on backend");
            }
        })
        .catch(err => console.error("Error updating contact status:", err));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Polling
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for dynamically added buttons
    document.getElementById('leads-table').addEventListener('click', handleWhatsAppClick);
});
