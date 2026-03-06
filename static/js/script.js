document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll endpoints every 30 seconds
    setInterval(fetchLeads, 30000);
    setInterval(fetchStats, 30000);

    // Event delegation for "Send WhatsApp" button clicks
    document.getElementById('leads-body').addEventListener('click', function(event) {
        if (event.target && event.target.classList.contains('whatsapp-btn')) {
            const btn = event.target;
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const message = btn.getAttribute('data-message');

            // Generate WhatsApp API URL
            const encodedMessage = encodeURIComponent(message);
            const waUrl = `https://wa.me/${phone.replace('+', '')}?text=${encodedMessage}`;

            // Open WhatsApp link synchronously to avoid browser popup blockers
            window.open(waUrl, '_blank');

            // Trigger backend status update
            markContacted(leadId);
        }
    });
});

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(data => {
            renderLeads(data);
        })
        .catch(error => console.error('Error fetching leads:', error));
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-leads').textContent = data.total;
            document.getElementById('contacted-leads').textContent = data.contacted;
            document.getElementById('new-leads').textContent = data.new;
        })
        .catch(error => console.error('Error fetching stats:', error));
}

function renderLeads(leads) {
    const tbody = document.getElementById('leads-body');
    tbody.innerHTML = ''; // Clear current

    leads.forEach(lead => {
        const tr = document.createElement('tr');

        // Dynamically build the WhatsApp message based on the type
        const message = buildWhatsAppMessage(lead);

        tr.innerHTML = `
            <td>${lead.business_name}</td>
            <td>${lead.type}</td>
            <td>${lead.city}</td>
            <td>${lead.phone}</td>
            <td>
                <button class="whatsapp-btn" data-id="${lead.id}" data-phone="${lead.phone}" data-message="${message}">
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function buildWhatsAppMessage(lead) {
    const type = lead.type.toLowerCase();
    let sector, entity, clients, action, focus;

    if (type === 'clinic') {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type === 'store') {
        sector = 'Retail';
        entity = 'Store';
        clients = 'Customers';
        action = 'buy products';
        focus = 'sales';
    } else {
        sector = 'Services';
        entity = 'Service';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    return `Hello ${lead.business_name} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on [Day of the Week]? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function markContacted(leadId) {
    fetch(`/api/contacted/${leadId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Re-fetch data to reflect changes
            fetchLeads();
            fetchStats();
        }
    })
    .catch(error => console.error('Error marking as contacted:', error));
}