document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-table-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp') || e.target.closest('.btn-whatsapp')) {
            const btn = e.target.classList.contains('btn-whatsapp') ? e.target : e.target.closest('.btn-whatsapp');
            const leadId = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            // 1. Generate message based on type
            const message = generateWhatsAppMessage(name, type);

            // 2. Open WhatsApp URL synchronously
            // Format phone: ensure it starts with country code without '+', but wa.me handles '+' well usually
            // However, to be safe, wa.me prefers just numbers.
            const cleanPhone = phone.replace(/\D/g, '');
            const waUrl = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;
            window.open(waUrl, '_blank');

            // 3. Update backend status (asynchronous)
            markLeadContacted(leadId, btn.closest('tr'));
        }
    });
});

function fetchStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-leads').innerText = data.total;
            document.getElementById('contacted-leads').innerText = data.contacted;
            document.getElementById('new-leads').innerText = data.new;
        })
        .catch(err => console.error('Error fetching stats:', err));
}

function fetchLeads() {
    fetch('/api/leads')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('leads-table-body');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No new leads found. Checking for updates...</td></tr>`;
                return;
            }

            data.forEach(lead => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHtml(lead.business_name)}</td>
                    <td>${escapeHtml(lead.type)}</td>
                    <td>${escapeHtml(lead.city)}</td>
                    <td>${escapeHtml(lead.phone)}</td>
                    <td>
                        <button class="btn-whatsapp"
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

function markLeadContacted(leadId, rowElement) {
    fetch(`/api/leads/${leadId}/contact`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // Remove row from UI
            rowElement.style.transition = 'opacity 0.5s';
            rowElement.style.opacity = '0';
            setTimeout(() => {
                rowElement.remove();
                fetchStats(); // Update counts
            }, 500);
        }
    })
    .catch(err => console.error('Error updating lead status:', err));
}

function generateWhatsAppMessage(businessName, businessType) {
    let sector = "Local Business";
    let entity = "Business";
    let clients = "Clients";
    let action = "utilize your services";
    let focus = "your core operations";

    const typeLower = businessType.toLowerCase();

    if (typeLower.includes('clinic')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower.includes('store') || typeLower.includes('retail')) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else if (typeLower.includes('service')) {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on [Day of the Week]? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
         .toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}