document.addEventListener('DOMContentLoaded', () => {
    const leadsTable = document.getElementById('leads-table');
    const leadsTbody = document.getElementById('leads-tbody');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');

    // Initial fetch
    fetchData();

    // Poll every 30 seconds
    setInterval(fetchData, 30000);

    function fetchData() {
        fetchStats();
        fetchLeads();
    }

    async function fetchStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            document.getElementById('stat-total').textContent = data.total || 0;
            document.getElementById('stat-contacted').textContent = data.contacted || 0;
            document.getElementById('stat-new').textContent = data.new || 0;
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    async function fetchLeads() {
        try {
            const response = await fetch('/api/leads');
            const leads = await response.json();

            loadingState.style.display = 'none';

            if (leads.length === 0) {
                leadsTable.style.display = 'none';
                emptyState.style.display = 'block';
            } else {
                leadsTable.style.display = 'table';
                emptyState.style.display = 'none';
                renderLeads(leads);
            }
        } catch (error) {
            console.error('Error fetching leads:', error);
            loadingState.style.display = 'none';
        }
    }

    function renderLeads(leads) {
        leadsTbody.innerHTML = '';

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.dataset.id = lead.id;

            const badgeClass = lead.type.toLowerCase();

            tr.innerHTML = `
                <td><strong>${lead.business_name}</strong></td>
                <td><span class="badge ${badgeClass}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp send-wa-btn"
                        data-id="${lead.id}"
                        data-name="${lead.business_name}"
                        data-type="${lead.type}"
                        data-phone="${lead.phone}">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                        </svg>
                        Send WhatsApp
                    </button>
                </td>
            `;
            leadsTbody.appendChild(tr);
        });
    }

    // Generate WhatsApp Message Template
    function generateMessage(businessName, businessType) {
        let entity, clients, action, focus;

        switch (businessType.toLowerCase()) {
            case 'clinic':
                entity = 'Clinic';
                clients = 'Patients';
                action = 'book appointments';
                focus = 'care';
                break;
            case 'store':
                entity = 'Store';
                clients = 'Customers';
                action = 'buy products';
                focus = 'sales';
                break;
            default:
                entity = 'Service';
                clients = 'Clients';
                action = 'book appointments';
                focus = 'services';
                break;
        }

        // Propose chat 2 days from now
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const d = new Date();
        d.setDate(d.getDate() + 2);
        const chatDay = days[d.getDay()];

        const message = `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${businessType} sector. Your establishment caught our attention due to its strong community presence! 🌟

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

    // Event delegation for WhatsApp buttons
    leadsTbody.addEventListener('click', async (e) => {
        const btn = e.target.closest('.send-wa-btn');
        if (!btn) return;

        const { id, name, type, phone } = btn.dataset;

        // Clean phone number (remove leading 0 and add country code if needed, assume PK +92)
        let formattedPhone = phone.replace(/[^0-9]/g, '');
        if (formattedPhone.startsWith('0')) {
            formattedPhone = '92' + formattedPhone.substring(1);
        } else if (!formattedPhone.startsWith('92')) {
            formattedPhone = '92' + formattedPhone;
        }

        const message = generateMessage(name, type);
        const waUrl = `https://wa.me/${formattedPhone}?text=${message}`;

        // Open WhatsApp
        window.open(waUrl, '_blank');

        // Optimistic UI update: Remove row
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
            row.style.opacity = '0.5';
            row.style.pointerEvents = 'none';
        }

        // Notify backend to mark as contacted
        try {
            await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lead_id: id })
            });

            // Re-fetch to sync exactly with server state
            fetchData();
        } catch (error) {
            console.error('Error updating lead status:', error);
            // Revert UI on error
            if (row) {
                row.style.opacity = '1';
                row.style.pointerEvents = 'auto';
            }
        }
    });
});
