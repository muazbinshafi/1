document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll for new leads every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for dynamically added WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-whatsapp');
        if (btn) {
            e.preventDefault(); // Prevent default link behavior
            const id = btn.getAttribute('data-id');
            const url = btn.getAttribute('href');

            // Synchronously open WhatsApp to avoid popup blockers
            window.open(url, '_blank', 'noopener,noreferrer');

            // Then make the background request to mark as contacted
            markAsContacted(id);
        }
    });
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('stat-total').textContent = stats.total;
        document.getElementById('stat-new').textContent = stats.new;
        document.getElementById('stat-contacted').textContent = stats.contacted;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeads() {
    const tbody = document.getElementById('leads-body');
    const loading = document.getElementById('loading');

    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        if (leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#666;">No uncontacted leads currently available.</td></tr>';
            return;
        }

        tbody.innerHTML = ''; // Clear existing

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-row-id', lead.id);

            // Determine styling based on type
            const typeClass = `type-${lead.type.toLowerCase()}`;

            // Generate WhatsApp message
            const message = generateWhatsAppMessage(lead.business_name, lead.type);
            const encodedMessage = encodeURIComponent(message);
            // Ensure phone is numeric for wa.me link
            const cleanPhone = lead.phone.replace(/[^0-9]/g, '');
            const waLink = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

            tr.innerHTML = `
                <td><strong>${lead.business_name}</strong></td>
                <td><span class="type-badge ${typeClass}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <a href="${waLink}" class="btn-whatsapp" data-id="${lead.id}">Send WhatsApp</a>
                </td>
            `;

            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('Error fetching leads:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:red;">Error loading leads.</td></tr>';
    }
}

async function markAsContacted(id) {
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: id })
        });

        if (response.ok) {
            // Remove the row from the table immediately for better UX
            const row = document.querySelector(`tr[data-row-id="${id}"]`);
            if (row) {
                row.remove();
            }
            // Update stats
            fetchStats();
        }
    } catch (error) {
        console.error('Error marking as contacted:', error);
    }
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
            clients = 'Customers';
            action = 'engage';
            focus = 'operations';
    }

    // Calculate a day two days from now for the chat proposition
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2);
    const chatDay = days[d.getDay()];

    return `Hello ${businessName} 👋,

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
}
