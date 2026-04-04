document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', (e) => {
        if (e.target.classList.contains('wa-btn')) {
            e.preventDefault(); // Prevent default link behavior if it's an 'a' tag

            const btn = e.target;
            const row = btn.closest('tr');
            const leadId = btn.getAttribute('data-id');
            const businessName = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            const message = generateWhatsAppMessage(businessName, type);
            const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;

            // Open WhatsApp synchronously to avoid popup blockers
            window.open(waUrl, '_blank');

            // Optimistic UI update: Remove row immediately
            row.remove();

            // Update stats optimistically
            const statNew = document.getElementById('stat-new');
            const statContacted = document.getElementById('stat-contacted');
            statNew.textContent = parseInt(statNew.textContent) - 1;
            statContacted.textContent = parseInt(statContacted.textContent) + 1;

            // Notify backend
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: leadId })
            }).catch(err => console.error('Error marking as contacted:', err));
        }
    });
});

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-new').textContent = data.new_leads;
            document.getElementById('stat-contacted').textContent = data.contacted;
        })
        .catch(err => console.error('Error fetching stats:', err));
}

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = '';

            if(data.length === 0) {
                 tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No new leads available. Background collector is running.</td></tr>';
                 return;
            }

            data.forEach(lead => {
                const tr = document.createElement('tr');

                const typeClass = `type-${lead.type.toLowerCase()}`;

                // Escape HTML to prevent XSS
                const escapeHtml = (unsafe) => {
                    return unsafe
                         .replace(/&/g, "&amp;")
                         .replace(/</g, "&lt;")
                         .replace(/>/g, "&gt;")
                         .replace(/"/g, "&quot;")
                         .replace(/'/g, "&#039;");
                 };

                tr.innerHTML = `
                    <td>${escapeHtml(lead.business_name)}</td>
                    <td><span class="type-badge ${typeClass}">${escapeHtml(lead.type)}</span></td>
                    <td>${escapeHtml(lead.city)}</td>
                    <td>${escapeHtml(lead.phone)}</td>
                    <td>
                        <button class="wa-btn"
                            data-id="${lead.id}"
                            data-name="${escapeHtml(lead.business_name)}"
                            data-type="${escapeHtml(lead.type)}"
                            data-phone="${escapeHtml(lead.phone)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error('Error fetching leads:', err));
}

function generateWhatsAppMessage(businessName, type) {
    let sector, entity, clients, action, focus;

    switch(type.toLowerCase()) {
        case 'clinic':
            sector = 'Healthcare';
            entity = 'Clinic';
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
            break;
        case 'store':
            sector = 'Retail';
            entity = 'Store';
            clients = 'Customers';
            action = 'browse products';
            focus = 'sales';
            break;
        case 'service':
            sector = 'Services';
            entity = 'Service';
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
            break;
        default:
            sector = 'Business';
            entity = 'Business';
            clients = 'Clients';
            action = 'discover your offerings';
            focus = 'operations';
    }

    // Calculate a day two days from now
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const date = new Date();
    date.setDate(date.getDate() + 2);
    const meetingDay = days[date.getDay()];

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${meetingDay}? 📞

Best regards,

MuazBinShafi
Owner | Business Solutions 💼`;
}