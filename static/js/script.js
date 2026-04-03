document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll for updates every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Use event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            e.preventDefault();
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            // 1. Open WhatsApp synchronously to avoid popup blockers
            const message = generateMessage(name, type);
            const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
            window.open(waUrl, '_blank');

            // 2. Optimistically remove the row from UI
            const row = btn.closest('tr');
            if (row) {
                row.remove();
            }

            // 3. Send API request to mark as contacted
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id: leadId })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    fetchStats(); // Update stats immediately
                }
            })
            .catch(err => console.error("Error marking contact:", err));
        }
    });
});

function escapeHtml(unsafe) {
    return (unsafe || "").toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            const loading = document.getElementById('loading-indicator');

            loading.classList.add('hidden');
            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted);">No new leads available. Searching...</td></tr>';
                return;
            }

            data.forEach(lead => {
                const tr = document.createElement('tr');
                tr.setAttribute('data-lead-id', lead.id);

                let badgeClass = 'type-service';
                if(lead.type === 'Clinic') badgeClass = 'type-clinic';
                if(lead.type === 'Store') badgeClass = 'type-store';

                tr.innerHTML = `
                    <td><strong>${escapeHtml(lead.business_name)}</strong></td>
                    <td><span class="type-badge ${badgeClass}">${escapeHtml(lead.type)}</span></td>
                    <td>${escapeHtml(lead.city)}</td>
                    <td>${escapeHtml(lead.phone)}</td>
                    <td>
                        <button class="btn-whatsapp"
                                data-id="${lead.id}"
                                data-phone="92${lead.phone.substring(1)}"
                                data-name="${escapeHtml(lead.business_name)}"
                                data-type="${escapeHtml(lead.type)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error("Error fetching leads:", err));
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stat-total').textContent = data.total || 0;
            document.getElementById('stat-new').textContent = data.new || 0;
            document.getElementById('stat-contacted').textContent = data.contacted || 0;
        })
        .catch(err => console.error("Error fetching stats:", err));
}

function getNextMeetingDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2); // 2 days from now
    return days[d.getDay()];
}

function generateMessage(businessName, businessType) {
    let sector = "Business";
    let entity = "business";
    let clients = "clients";
    let action = "book appointments";
    let focus = "services";

    if (businessType === "Clinic") {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (businessType === "Store") {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    } else {
        sector = "Service";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const day = getNextMeetingDay();

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}
