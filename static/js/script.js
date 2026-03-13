document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('leads-body');
    const statTotal = document.getElementById('stat-total');
    const statNew = document.getElementById('stat-new');
    const statContacted = document.getElementById('stat-contacted');
    const refreshBtn = document.getElementById('refresh-btn');

    const terminology = {
        'Clinic': {
            entity: 'Clinic',
            clients: 'Patients',
            action: 'book appointments',
            focus: 'care',
            sector: 'Healthcare'
        },
        'Store': {
            entity: 'Store',
            clients: 'Customers',
            action: 'buy products',
            focus: 'sales',
            sector: 'Retail'
        },
        'Service': {
            entity: 'Service',
            clients: 'Clients',
            action: 'book appointments',
            focus: 'services',
            sector: 'Services'
        }
    };

    function getNextDayOfWeek() {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const targetDate = new Date();
        targetDate.setDate(targetDate.getDate() + 2); // 2 days from now
        return days[targetDate.getDay()];
    }

    function generateMessage(lead) {
        const type = lead.type || 'Service';
        const terms = terminology[type] || terminology['Service'];
        const chatDay = getNextDayOfWeek();

        const message = `Hello ${lead.business_name} 👋,\n\nThis is MuazBinShafi, Owner of Business Solutions 🏢.\nI hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${terms.sector} sector. Your establishment caught our attention due to its strong community presence! 🌟\n\n*The Digital Opportunity 📈*\nIn our research, we noticed that many businesses like yours are thriving with an online presence, while your ${terms.entity} currently lacks a dedicated website.\n\n*Your 24/7 Digital Partner 🕒*\nIn today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${terms.clients} discover your services and ${terms.action} while you focus on ${terms.focus}. 💻✨\n\n*Why Business Solutions?*\n✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.\n🌐 *Digital Transformation:* We can elevate your ${terms.entity} to become a recognized 'Digital Brand.'\n🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.\n\nI would love to discuss how we can help your ${terms.entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞\n\nBest regards,\nMuazBinShafi\nOwner | Business Solutions 💼`;

        return encodeURIComponent(message);
    }

    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            statTotal.textContent = data.total || 0;
            statNew.textContent = data.new || 0;
            statContacted.textContent = data.contacted || 0;
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    async function fetchLeads() {
        refreshBtn.classList.add('loading');
        try {
            const response = await fetch('/api/leads');
            const leads = await response.json();

            tableBody.innerHTML = '';

            if (leads.length === 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="5" class="empty-state">No active leads found. Checking for new businesses...</td>`;
                tableBody.appendChild(tr);
            } else {
                leads.forEach(lead => {
                    const tr = document.createElement('tr');
                    tr.dataset.id = lead.id;

                    const message = generateMessage(lead);
                    const rawPhone = lead.phone.replace(/[^0-9]/g, '');
                    const whatsappUrl = `https://wa.me/${rawPhone}?text=${message}`;

                    tr.innerHTML = `
                        <td>${lead.business_name}</td>
                        <td>${lead.type}</td>
                        <td>${lead.city}</td>
                        <td>${lead.phone}</td>
                        <td>
                            <button class="btn-whatsapp" data-url="${whatsappUrl}">
                                Send WhatsApp
                            </button>
                        </td>
                    `;
                    tableBody.appendChild(tr);
                });
            }
        } catch (error) {
            console.error('Error fetching leads:', error);
        } finally {
            refreshBtn.classList.remove('loading');
        }
    }

    async function handleAction(e) {
        if (e.target.closest('.btn-whatsapp')) {
            const btn = e.target.closest('.btn-whatsapp');
            const row = btn.closest('tr');
            const leadId = row.dataset.id;
            const url = btn.dataset.url;

            // Open WhatsApp synchronously before async call
            window.open(url, '_blank', 'noopener,noreferrer');

            try {
                // Update backend immediately
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ id: parseInt(leadId) })
                });

                if (response.ok) {
                    // Remove from view instantly
                    row.remove();
                    // Update stats asynchronously
                    fetchStats();

                    if (tableBody.children.length === 0) {
                        tableBody.innerHTML = `<tr><td colspan="5" class="empty-state">All caught up! Waiting for new leads...</td></tr>`;
                    }
                }
            } catch (error) {
                console.error('Error updating lead status:', error);
            }
        }
    }

    // Event Listeners
    refreshBtn.addEventListener('click', () => {
        fetchStats();
        fetchLeads();
    });

    tableBody.addEventListener('click', handleAction);

    // Initial Load
    fetchStats();
    fetchLeads();

    // Polling
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);
});
