document.addEventListener('DOMContentLoaded', () => {
    const leadsBody = document.getElementById('leads-body');
    const statTotal = document.getElementById('stat-total');
    const statNew = document.getElementById('stat-new');
    const statContacted = document.getElementById('stat-contacted');

    // Polling intervals
    fetchLeads();
    fetchStats();
    setInterval(fetchLeads, 30000); // 30 seconds
    setInterval(fetchStats, 30000);

    function fetchLeads() {
        fetch('/api/leads')
            .then(res => res.json())
            .then(data => {
                renderLeads(data);
            })
            .catch(err => console.error('Error fetching leads:', err));
    }

    function fetchStats() {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                statTotal.textContent = data.total_leads;
                statNew.textContent = data.new_leads;
                statContacted.textContent = data.contacted_leads;
            })
            .catch(err => console.error('Error fetching stats:', err));
    }

    function renderLeads(leads) {
        if (leads.length === 0) {
            leadsBody.innerHTML = '<tr><td colspan="5" class="loading">No new leads available. Checking for more...</td></tr>';
            return;
        }

        leadsBody.innerHTML = leads.map(lead => `
            <tr data-id="${lead.id}">
                <td><strong>${escapeHTML(lead.business_name)}</strong></td>
                <td><span class="type-badge type-${escapeHTML(lead.type)}">${escapeHTML(lead.type)}</span></td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp" data-id="${lead.id}" data-name="${escapeHTML(lead.business_name)}" data-type="${escapeHTML(lead.type)}" data-phone="${escapeHTML(lead.phone)}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232"/>
                        </svg>
                        Send WhatsApp
                    </button>
                </td>
            </tr>
        `).join('');
    }

    function escapeHTML(str) {
        return String(str).replace(/[&<>'"]/g,
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    function generateMessage(businessName, type) {
        let sector = type;
        let entity = type;
        let clients = "Clients";
        let action = "book appointments";
        let focus = "services";

        if (type === "Clinic") {
            clients = "Patients";
            action = "book appointments";
            focus = "care";
        } else if (type === "Store") {
            clients = "Customers";
            action = "buy products";
            focus = "sales";
        } else if (type === "Service") {
            clients = "Clients";
            action = "book appointments";
            focus = "services";
        }

        // Calculate day 2 days from now
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const d = new Date();
        d.setDate(d.getDate() + 2);
        const dayOfWeek = days[d.getDay()];

        const msg = `Hello ${businessName} 👋,
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

        return encodeURIComponent(msg);
    }

    // Event delegation for WhatsApp buttons
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-whatsapp');
        if (!btn) return;

        const id = btn.dataset.id;
        const name = btn.dataset.name;
        const type = btn.dataset.type;
        const phone = btn.dataset.phone;

        // Clean phone number for wa.me link
        const cleanPhone = phone.replace(/[^0-9]/g, '');
        const message = generateMessage(name, type);
        const waUrl = `https://wa.me/${cleanPhone}?text=${message}`;

        // Open WhatsApp
        window.open(waUrl, '_blank');

        // Mark as contacted in backend
        fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ lead_id: id })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                // Remove row from table immediately for good UX
                const row = document.querySelector(`tr[data-id="${id}"]`);
                if (row) row.remove();

                // Refresh stats
                fetchStats();

                // If empty, show loading
                if (document.querySelectorAll('#leads-body tr').length === 0) {
                    leadsBody.innerHTML = '<tr><td colspan="5" class="loading">No new leads available. Checking for more...</td></tr>';
                }
            }
        })
        .catch(err => console.error('Error updating lead:', err));
    });
});
