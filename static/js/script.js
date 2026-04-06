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
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            sendWhatsApp(leadId, phone, name, type, btn.closest('tr'));
        }
    });
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

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        document.getElementById('total-leads').innerText = data.total;
        document.getElementById('new-leads').innerText = data.new;
        document.getElementById('contacted-leads').innerText = data.contacted;
    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        const tbody = document.getElementById('leads-body');

        if (leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No new leads available at the moment.</td></tr>';
            return;
        }

        tbody.innerHTML = leads.map(lead => `
            <tr id="lead-${lead.id}">
                <td>${escapeHTML(lead.business_name)}</td>
                <td>${escapeHTML(lead.type)}</td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp"
                            data-id="${lead.id}"
                            data-phone="${escapeHTML(lead.phone)}"
                            data-name="${escapeHTML(lead.business_name)}"
                            data-type="${escapeHTML(lead.type)}">
                        Send WhatsApp
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error("Error fetching leads:", error);
    }
}

function getPitchTemplate(name, type) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2);
    const dayOfWeek = days[d.getDay()];

    let sector = type;
    let entity = type;
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";

    if (type.toLowerCase() === 'clinic') {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type.toLowerCase() === 'store') {
        sector = 'Retail';
        entity = 'Store';
        clients = 'Customers';
        action = 'buy products';
        focus = 'sales';
    } else if (type.toLowerCase() === 'service') {
        sector = 'Services';
        entity = 'Service';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

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

function sendWhatsApp(id, phone, name, type, rowElement) {
    // Sanitize phone number (remove hyphens, spaces, and specifically leading zero)
    let cleanPhone = phone.replace(/[-\s]/g, '');
    cleanPhone = cleanPhone.replace(/^0/, '');

    // Assuming Pakistan country code
    const fullPhone = `92${cleanPhone}`;

    const message = encodeURIComponent(getPitchTemplate(name, type));
    const url = `https://wa.me/${fullPhone}?text=${message}`;

    // Open WhatsApp URL synchronously
    window.open(url, '_blank');

    // Optimistic UI update
    rowElement.remove();

    // Update backend asynchronously
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: parseInt(id) })
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            fetchStats(); // Update stats
        }
    })
    .catch((error) => {
        console.error('Error marking as contacted:', error);
        // Could revert UI here if needed, but keeping it simple
    });
}
