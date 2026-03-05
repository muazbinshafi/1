document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Auto-refresh every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event delegation for the WhatsApp button
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('whatsapp-btn')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            // Generate WhatsApp URL
            const url = generateWhatsAppLink(name, type, phone);

            // Open WhatsApp immediately
            window.open(url, '_blank');

            // Then mark as contacted via backend
            markAsContacted(id, btn.closest('tr'));
        }
    });
});

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = '';

            data.forEach(lead => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${lead.business_name}</td>
                    <td>${lead.type}</td>
                    <td>${lead.city}</td>
                    <td>${lead.phone}</td>
                    <td>
                        <button class="whatsapp-btn"
                                data-id="${lead.id}"
                                data-name="${lead.business_name}"
                                data-type="${lead.type}"
                                data-phone="${lead.phone}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => console.error('Error fetching leads:', error));
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-new').textContent = data.new;
            document.getElementById('stat-contacted').textContent = data.contacted;
        })
        .catch(error => console.error('Error fetching stats:', error));
}

function markAsContacted(id, rowElement) {
    fetch(`/api/contacted/${id}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Remove row from table
                rowElement.remove();
                // Update stats
                fetchStats();
            }
        })
        .catch(error => console.error('Error marking as contacted:', error));
}

function generateWhatsAppLink(businessName, type, phone) {
    let sector = '';
    let entity = '';
    let clients = '';
    let action = '';
    let focus = '';

    const lowerType = type.toLowerCase();

    if (lowerType.includes('clinic')) {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (lowerType.includes('store')) {
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

    const nextMonday = getNextMonday();

    const message = `Hello ${businessName} 👋,
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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${nextMonday}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    // Ensure phone number is formatted for WhatsApp (e.g., removing '+' and spaces)
    const formattedPhone = phone.replace(/[^0-9]/g, '');

    return `https://wa.me/${formattedPhone}?text=${encodeURIComponent(message)}`;
}

function getNextMonday() {
    const d = new Date();
    d.setDate(d.getDate() + (1 + 7 - d.getDay()) % 7 || 7);
    const options = { weekday: 'long' };
    return d.toLocaleDateString('en-US', options);
}