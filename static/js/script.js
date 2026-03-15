document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const leadsBody = document.getElementById('leads-body');
    const refreshBtn = document.getElementById('refresh-btn');
    const metricTotal = document.getElementById('metric-total');
    const metricContacted = document.getElementById('metric-contacted');
    const metricNew = document.getElementById('metric-new');

    // Fetch initial data
    fetchStats();
    fetchLeads();

    // Auto-refresh data every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Refresh button event listener
    refreshBtn.addEventListener('click', () => {
        fetchStats();
        fetchLeads();

        // Visual feedback
        refreshBtn.textContent = 'Refreshing...';
        refreshBtn.disabled = true;
        setTimeout(() => {
            refreshBtn.textContent = 'Refresh Leads';
            refreshBtn.disabled = false;
        }, 1000);
    });

    // Event Delegation for "Send WhatsApp" buttons
    leadsBody.addEventListener('click', async (e) => {
        const btn = e.target.closest('.wa-btn');
        if (!btn) return;

        const row = btn.closest('tr');
        const id = row.dataset.id;
        const name = row.dataset.name;
        const type = row.dataset.type;
        const phone = row.dataset.phone;

        // Construct message
        const message = generatePitch(name, type);

        // Encode URI safely for URL appending
        const encodedMessage = encodeURIComponent(message);

        // Prepare formatted phone for URL
        let formattedPhone = phone.replace(/[^0-9]/g, '');
        if (formattedPhone.startsWith('0')) {
            formattedPhone = '92' + formattedPhone.substring(1);
        }

        const waUrl = `https://wa.me/${formattedPhone}?text=${encodedMessage}`;

        // Open WhatsApp link synchronously before triggering backend call
        window.open(waUrl, '_blank');

        // Backend call to mark as contacted
        await markAsContacted(id, row);
    });

    // Fetch dashboard metrics
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (res.ok) {
                const data = await res.json();
                metricTotal.textContent = data.total;
                metricContacted.textContent = data.contacted;
                metricNew.textContent = data.new_leads;
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    // Fetch active leads table data
    async function fetchLeads() {
        try {
            const res = await fetch('/api/leads');
            if (res.ok) {
                const leads = await res.json();
                renderLeads(leads);
            }
        } catch (error) {
            console.error('Error fetching leads:', error);
            leadsBody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:red;">Failed to load leads. Backend may be down.</td></tr>';
        }
    }

    // Render table rows
    function renderLeads(leads) {
        if (leads.length === 0) {
            leadsBody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:2rem;">No new leads available without websites. Waiting for collector to run...</td></tr>';
            return;
        }

        leadsBody.innerHTML = leads.map(lead => `
            <tr data-id="${lead.id}" data-name="${lead.business_name}" data-type="${lead.type}" data-phone="${lead.phone}">
                <td style="font-weight: 600;">${lead.business_name}</td>
                <td><span class="type-badge type-${lead.type}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td style="font-family: monospace; font-size: 1.1rem;">${lead.phone}</td>
                <td>
                    <button class="wa-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                        </svg>
                        Send WhatsApp
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Call backend API to update status, then update UI
    async function markAsContacted(id, rowElement) {
        try {
            const res = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id })
            });

            if (res.ok) {
                // visually remove the row
                rowElement.style.opacity = '0.5';
                rowElement.style.transition = 'opacity 0.5s ease-out';
                setTimeout(() => {
                    rowElement.remove();
                    // Refetch stats to keep numbers accurate
                    fetchStats();

                    // Check if table empty after removal
                    if (leadsBody.children.length === 0) {
                        fetchLeads();
                    }
                }, 500);
            }
        } catch (error) {
            console.error('Error marking as contacted:', error);
        }
    }

    // Pitch Template generation based on dynamic rules
    function generatePitch(businessName, type) {
        // Default terms
        let terms = {
            sector: type,
            entity: type.toLowerCase(),
            clients: "Clients",
            action: "book appointments",
            focus: "services"
        };

        if (type.toLowerCase() === 'clinic') {
            terms = {
                sector: "Healthcare",
                entity: "Clinic",
                clients: "Patients",
                action: "book appointments",
                focus: "care"
            };
        } else if (type.toLowerCase() === 'store') {
            terms = {
                sector: "Retail",
                entity: "Store",
                clients: "Customers",
                action: "browse products",
                focus: "sales"
            };
        } else if (type.toLowerCase() === 'service') {
            terms = {
                sector: "Services",
                entity: "Service Provider",
                clients: "Clients",
                action: "book appointments",
                focus: "services"
            };
        }

        // Calculate 2 days from now for chat proposal
        const date = new Date();
        date.setDate(date.getDate() + 2);
        const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        const proposedDay = dayNames[date.getDay()];

        return `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${terms.sector} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${terms.entity} currently lacks a dedicated website.

*Your 24/7 Digital Partner 🕒*
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${terms.clients} discover your services and ${terms.action} while you focus on ${terms.focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${terms.entity} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${terms.entity} thrive online. Are you available for a brief chat on ${proposedDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
    }
});
