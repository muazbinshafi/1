document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.closest('.btn-whatsapp')) {
            const btn = e.target.closest('.btn-whatsapp');
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const businessName = btn.getAttribute('data-name');
            const businessType = btn.getAttribute('data-type');

            // Format WhatsApp URL and open synchronously before API call
            const url = generateWhatsAppLink(phone, businessName, businessType);
            window.open(url, '_blank');

            // Mark as contacted and remove from UI
            markContacted(leadId, btn.closest('tr'));
        }
    });
});

function getChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2);
    return days[d.getDay()];
}

function generateWhatsAppLink(phone, businessName, businessType) {
    let sector = "Business";
    let entity = "Business";
    let clients = "Clients";
    let action = "utilize your services";
    let focus = "your core operations";

    if (businessType.toLowerCase() === 'clinic') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (businessType.toLowerCase() === 'store') {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    } else if (businessType.toLowerCase() === 'service') {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const day = getChatDay();

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞

Best regards,

MuazBinShafi
Owner | Business Solutions 💼`;

    const encodedMessage = encodeURIComponent(template);
    // Remove '+' and '-' from phone number for the wa.me link
    const cleanPhone = phone.replace(/\\D/g, '');
    return `https://wa.me/${cleanPhone}?text=${encodedMessage}`;
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        const tbody = document.getElementById('leads-body');
        const loading = document.getElementById('loading');
        const noLeads = document.getElementById('no-leads');

        loading.classList.add('hidden');

        if (leads.length === 0) {
            tbody.innerHTML = '';
            noLeads.classList.remove('hidden');
            return;
        }

        noLeads.classList.add('hidden');

        tbody.innerHTML = '';
        leads.forEach(lead => {
            const tr = document.createElement('tr');
            const typeClass = `type-${lead.type.toLowerCase()}`;

            tr.innerHTML = `
                <td><strong>${lead.business_name}</strong></td>
                <td><span class="badge ${typeClass}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp"
                        data-id="${lead.id}"
                        data-phone="${lead.phone}"
                        data-name="${lead.business_name}"
                        data-type="${lead.type}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('total-leads').textContent = stats.total;
        document.getElementById('contacted-leads').textContent = stats.contacted;
        document.getElementById('new-leads').textContent = stats.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function markContacted(id, rowElement) {
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        });

        if (response.ok) {
            rowElement.remove();
            fetchStats();

            const tbody = document.getElementById('leads-body');
            if (tbody.children.length === 0) {
                document.getElementById('no-leads').classList.remove('hidden');
            }
        }
    } catch (error) {
        console.error('Error marking as contacted:', error);
    }
}
