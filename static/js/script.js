document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll for updates every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('total-leads').textContent = data.total;
        document.getElementById('contacted-leads').textContent = data.contacted;
        document.getElementById('new-leads').textContent = data.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        const tbody = document.querySelector('#leads-table tbody');
        tbody.innerHTML = ''; // Clear existing rows

        document.getElementById('loading').style.display = 'none';

        leads.forEach(lead => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${lead.business_name}</td>
                <td>${lead.type}</td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="whatsapp-btn" onclick="sendWhatsApp(${lead.id}, '${lead.business_name}', '${lead.type}', '${lead.phone}')">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        if (leads.length === 0) {
             document.getElementById('loading').style.display = 'block';
             document.getElementById('loading').textContent = 'No new leads available.';
        }

    } catch (error) {
        console.error('Error fetching leads:', error);
        document.getElementById('loading').textContent = 'Error loading leads.';
    }
}

function sendWhatsApp(id, name, type, phone) {
    // Determine dynamic variables based on type
    let entity = type;
    let clients = 'Clients';
    let action = 'book appointments';
    let focus = 'services';

    if (type.toLowerCase() === 'clinic') {
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type.toLowerCase() === 'store') {
        clients = 'Customers';
        action = 'buy products';
        focus = 'sales';
    } else if (type.toLowerCase() === 'service') {
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const day = new Date().toLocaleDateString('en-US', { weekday: 'long' });

    // Template
    const message = `Hello ${name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${type} sector. Your establishment caught our attention due to its strong community presence! 🌟

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

    // Encode message for URL
    const encodedMessage = encodeURIComponent(message);

    // Construct WhatsApp URL
    // Removing dashes from phone for safety, assuming standard format
    const cleanPhone = phone.replace(/-/g, '').replace(/\s/g, '');
    const url = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

    // Mark as contacted in backend
    fetch(`/api/contact/${id}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Open WhatsApp in new tab
                window.open(url, '_blank');
                // Refresh dashboard to remove the lead
                fetchStats();
                fetchLeads();
            }
        })
        .catch(err => console.error('Error marking contacted:', err));
}
