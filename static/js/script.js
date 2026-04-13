document.addEventListener('DOMContentLoaded', () => {
    const leadsBody = document.getElementById('leads-body');
    const statTotal = document.getElementById('stat-total');
    const statNew = document.getElementById('stat-new');
    const statContacted = document.getElementById('stat-contacted');
    const loading = document.getElementById('loading');

    let isFetching = false;

    // Utility: HTML escape to prevent XSS
    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function fetchData() {
        if (isFetching) return;
        isFetching = true;

        try {
            // Fetch stats
            const statsRes = await fetch('/api/stats');
            if (statsRes.ok) {
                const stats = await statsRes.json();
                statTotal.textContent = stats.total;
                statNew.textContent = stats.new;
                statContacted.textContent = stats.contacted;
            }

            // Fetch leads
            const leadsRes = await fetch('/api/leads');
            if (leadsRes.ok) {
                const leads = await leadsRes.json();
                renderLeads(leads);
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            isFetching = false;
        }
    }

    function renderLeads(leads) {
        if (leads.length === 0) {
            leadsBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No active leads found.</td></tr>';
            return;
        }

        leadsBody.innerHTML = leads.map(lead => `
            <tr data-id="${lead.id}">
                <td>${escapeHTML(lead.business_name)}</td>
                <td>${escapeHTML(lead.type)}</td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp" data-action="whatsapp"
                        data-id="${lead.id}"
                        data-name="${escapeHTML(lead.business_name)}"
                        data-type="${escapeHTML(lead.type)}"
                        data-phone="${escapeHTML(lead.phone)}">
                        Send WhatsApp
                    </button>
                </td>
            </tr>
        `).join('');
    }

    function getPitch(name, type) {
        let entity = "Business";
        let clients = "Clients";
        let action = "discover services";
        let focus = "operations";
        let sector = "Local";

        if (type.toLowerCase().includes('clinic')) {
            entity = "Clinic";
            clients = "Patients";
            action = "book appointments";
            focus = "care";
            sector = "Healthcare";
        } else if (type.toLowerCase().includes('store')) {
            entity = "Store";
            clients = "Customers";
            action = "buy products";
            focus = "sales";
            sector = "Retail";
        } else if (type.toLowerCase().includes('service')) {
            entity = "Service";
            clients = "Clients";
            action = "book appointments";
            focus = "services";
            sector = "Services";
        }

        // Calculate a day, e.g., 2 days from now
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const date = new Date();
        date.setDate(date.getDate() + 2);
        const chatDay = days[date.getDay()];

        const message = `Hello ${name} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

        return encodeURIComponent(message);
    }

    // Event Delegation for "Send WhatsApp"
    leadsBody.addEventListener('click', async (e) => {
        if (e.target && e.target.getAttribute('data-action') === 'whatsapp') {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            let rawPhone = btn.getAttribute('data-phone');

            // Sanitize phone for Pakistan: remove spaces, dashes, leading zero, prepend 92
            const cleanPhone = "92" + rawPhone.replace(/[-\s]/g, '').replace(/^0/, '');
            const message = getPitch(name, type);
            const url = `https://wa.me/${cleanPhone}?text=${message}`;

            // Open WhatsApp synchronously to avoid popup blockers
            window.open(url, '_blank');

            // Optimistic UI update: Remove row immediately
            const row = btn.closest('tr');
            if (row) row.remove();

            // Update stats optimistically
            const newCount = parseInt(statNew.textContent) - 1;
            const contactedCount = parseInt(statContacted.textContent) + 1;
            statNew.textContent = newCount >= 0 ? newCount : 0;
            statContacted.textContent = contactedCount;

            // Notify backend
            try {
                await fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id })
                });
                // Fetch fresh data in background
                fetchData();
            } catch (error) {
                console.error('Error marking as contacted:', error);
            }
        }
    });

    // Initial fetch
    fetchData();

    // Poll every 30 seconds
    setInterval(fetchData, 30000);
});