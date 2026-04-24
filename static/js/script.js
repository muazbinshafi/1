document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('leads-body');
    const table = document.getElementById('leads-table');
    const loading = document.getElementById('loading');
    const emptyState = document.getElementById('empty-state');
    const totalLeadsEl = document.getElementById('total-leads');
    const contactedLeadsEl = document.getElementById('contacted-leads');

    let sessionContacted = 0;

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getChatDay() {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const date = new Date();
        date.setDate(date.getDate() + 2);
        return days[date.getDay()];
    }

    function generateMessage(lead) {
        const name = escapeHtml(lead.name);
        const type = lead.type || 'Service';
        let entity, clients, action, focus, sector;

        if (type.toLowerCase() === 'clinic') {
            entity = 'Clinic';
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
            sector = 'Healthcare';
        } else if (type.toLowerCase() === 'store') {
            entity = 'Store';
            clients = 'Customers';
            action = 'buy products';
            focus = 'sales';
            sector = 'Retail';
        } else {
            entity = 'Service';
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
            sector = 'Services';
        }

        const chatDay = getChatDay();

        const msg = `Hello ${name} 👋,
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

        return encodeURIComponent(msg);
    }

    function formatPhone(phone) {
        return phone.replace(/[-\s]/g, '').replace(/^0/, '92');
    }

    function renderLeads(leads) {
        loading.style.display = 'none';

        if (leads.length === 0) {
            table.style.display = 'none';
            emptyState.style.display = 'block';
            totalLeadsEl.textContent = '0';
            return;
        }

        table.style.display = 'table';
        emptyState.style.display = 'none';
        totalLeadsEl.textContent = leads.length;

        tableBody.innerHTML = '';
        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.dataset.id = lead.id;

            const formattedPhone = formatPhone(lead.phone);
            const msg = generateMessage(lead);
            const waUrl = `https://wa.me/${formattedPhone}?text=${msg}`;

            tr.innerHTML = `
                <td>${escapeHtml(lead.name)}</td>
                <td>${escapeHtml(lead.type)}</td>
                <td>${escapeHtml(lead.city)}</td>
                <td>${escapeHtml(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp" data-id="${lead.id}" data-url="${waUrl}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    }

    function fetchLeads() {
        fetch('/api/leads')
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data)) {
                    renderLeads(data);
                }
            })
            .catch(err => {
                console.error("Error fetching leads:", err);
                loading.textContent = "Error loading leads.";
            });
    }

    // Event delegation for WhatsApp buttons
    tableBody.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.dataset.id;
            const url = btn.dataset.url;

            // Open WA synchronously
            window.open(url, '_blank');

            // Optimistic UI update
            const row = btn.closest('tr');
            if (row) {
                row.remove();

                // Update stats
                sessionContacted++;
                contactedLeadsEl.textContent = sessionContacted;

                let currentTotal = parseInt(totalLeadsEl.textContent, 10);
                if (!isNaN(currentTotal) && currentTotal > 0) {
                    currentTotal--;
                    totalLeadsEl.textContent = currentTotal;
                }

                if (currentTotal === 0) {
                    table.style.display = 'none';
                    emptyState.style.display = 'block';
                }
            }

            // Backend update
            fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: parseInt(leadId, 10) })
            }).catch(err => console.error("Error updating lead status:", err));
        }
    });

    // Initial fetch
    fetchLeads();

    // Poll for new leads every 30 seconds
    setInterval(fetchLeads, 30000);
});