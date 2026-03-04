document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll for new leads every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event Delegation for "Send WhatsApp" buttons
    document.getElementById('leads-tbody').addEventListener('click', handleWhatsAppClick);
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('stat-total').textContent = stats.total;
        document.getElementById('stat-contacted').textContent = stats.contacted;
        document.getElementById('stat-new').textContent = stats.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        renderLeadsTable(leads);
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById('leads-tbody');
    const table = document.getElementById('leads-table');
    const noLeadsMsg = document.getElementById('no-leads-message');

    tbody.innerHTML = '';

    if (leads.length === 0) {
        table.classList.add('hidden');
        noLeadsMsg.classList.remove('hidden');
        return;
    }

    table.classList.remove('hidden');
    noLeadsMsg.classList.add('hidden');

    leads.forEach(lead => {
        const tr = document.createElement('tr');

        // Ensure consistent casing for classes
        const typeClass = `type-${lead.type.toLowerCase()}`;

        tr.innerHTML = `
            <td><strong>${lead.business_name}</strong></td>
            <td><span class="type-badge ${typeClass}">${lead.type}</span></td>
            <td>${lead.city}</td>
            <td>${lead.phone}</td>
            <td>
                <button class="btn-whatsapp"
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
}

function handleWhatsAppClick(event) {
    const btn = event.target.closest('.btn-whatsapp');
    if (!btn) return;

    const id = btn.getAttribute('data-id');
    const name = btn.getAttribute('data-name');
    const type = btn.getAttribute('data-type');
    let phone = btn.getAttribute('data-phone');

    // Ensure phone number has no spaces and uses digits only + optional +
    phone = phone.replace(/[^\d+]/g, '');

    const message = generateMessage(name, type);
    const whatsappUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;

    // Open WhatsApp URL (must be done synchronously inside the click handler to avoid popup blockers)
    window.open(whatsappUrl, '_blank');

    // Trigger backend update to mark as contacted
    markAsContacted(id, btn);
}

function generateMessage(businessName, businessType) {
    // Determine dynamic terms based on business type
    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    if (businessType === "Clinic") {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (businessType === "Service") {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const dayOfWeek = new Date(Date.now() + 86400000).toLocaleDateString('en-US', { weekday: 'long' }); // Tomorrow

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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

async function markAsContacted(leadId, buttonElement) {
    try {
        const response = await fetch(`/api/leads/${leadId}/contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Remove the row from the UI
            const tr = buttonElement.closest('tr');
            if (tr) {
                tr.remove();

                // If no more rows, show the empty message
                const tbody = document.getElementById('leads-tbody');
                if (tbody.children.length === 0) {
                    document.getElementById('leads-table').classList.add('hidden');
                    document.getElementById('no-leads-message').classList.remove('hidden');
                }
            }
            // Refresh stats to reflect the change
            fetchStats();
        }
    } catch (error) {
        console.error('Failed to mark lead as contacted:', error);
    }
}
