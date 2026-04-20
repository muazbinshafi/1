document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const rawPhone = btn.getAttribute('data-phone');

            // Format phone for wa.me
            const phone = rawPhone.replace(/[-\s]/g, '').replace(/^0/, '92');

            // Determine terminology based on business type
            let clientsTerm = "Clients";
            let actionTerm = "book appointments";
            let focusTerm = "services";
            let entityTerm = "Service";
            let sectorTerm = "Services";

            if (type.toLowerCase().includes('clinic')) {
                clientsTerm = "Patients";
                actionTerm = "book appointments";
                focusTerm = "care";
                entityTerm = "Clinic";
                sectorTerm = "Healthcare";
            } else if (type.toLowerCase().includes('retail')) {
                clientsTerm = "Customers";
                actionTerm = "buy products";
                focusTerm = "sales";
                entityTerm = "Store";
                sectorTerm = "Retail";
            }

            // Calculate day (+2 days from now)
            const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const today = new Date();
            const futureDate = new Date(today);
            futureDate.setDate(today.getDate() + 2);
            const targetDay = days[futureDate.getDay()];

            // Construct the message using native WhatsApp *bold* syntax
            const message = `Hello ${name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I'm reaching out because my team and I have been analyzing prominent businesses within the ${sectorTerm} sector. Your establishment caught our attention due to its strong community presence! 🌟
*The Digital Opportunity* 📈
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entityTerm} currently lacks a dedicated website.
*Your 24/7 Digital Partner* 🕒
In today's digital world, a website acts as your most reliable assistant—it's available 24/7 to help ${clientsTerm} discover your services and ${actionTerm} while you focus on ${focusTerm}. 💻✨
*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${entityTerm} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${entityTerm} thrive online. Are you available for a brief chat on ${targetDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

            const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;

            // Open WhatsApp synchronously to prevent popup blockers
            window.open(waUrl, '_blank');

            // Optimistic UI update: Remove row immediately
            const row = btn.closest('tr');
            if (row) {
                row.remove();
            }

            // Notify backend
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: leadId })
            }).then(() => {
                fetchStats();
            }).catch(err => console.error("Error updating lead status:", err));
        }
    });
});

function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
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
            tbody.innerHTML = '';

            data.forEach(lead => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHTML(lead.name)}</td>
                    <td>${escapeHTML(lead.type)}</td>
                    <td>${escapeHTML(lead.city)}</td>
                    <td>${escapeHTML(lead.phone)}</td>
                    <td>
                        <button class="btn-whatsapp"
                            data-id="${lead.id}"
                            data-name="${escapeHTML(lead.name)}"
                            data-type="${escapeHTML(lead.type)}"
                            data-phone="${escapeHTML(lead.phone)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error('Error fetching leads:', err));
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-leads').textContent = data.total;
            document.getElementById('active-leads').textContent = data.active;
            document.getElementById('contacted-leads').textContent = data.contacted;
        })
        .catch(err => console.error('Error fetching stats:', err));
}