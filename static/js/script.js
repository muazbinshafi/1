document.addEventListener('DOMContentLoaded', () => {
    const leadsTableBody = document.getElementById('leads-table-body');
    const statTotal = document.getElementById('stat-total');
    const statContacted = document.getElementById('stat-contacted');
    const statNew = document.getElementById('stat-new');

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            statTotal.textContent = data.Total || 0;
            statContacted.textContent = data.Contacted || 0;
            statNew.textContent = data.New || 0;
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    const fetchLeads = async () => {
        try {
            const response = await fetch('/api/leads');
            const leads = await response.json();
            renderLeads(leads);
        } catch (error) {
            console.error('Error fetching leads:', error);
            leadsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Error loading leads</td></tr>';
        }
    };

    const generateWhatsAppMessage = (lead) => {
        const d = new Date();
        d.setDate(d.getDate() + 2); // Propose chat day 2 days from now
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = days[d.getDay()];

        let sector, entity, clients, action, focus;

        if (lead.type.toLowerCase() === 'clinic') {
            sector = 'Healthcare';
            entity = 'Clinic';
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
        } else if (lead.type.toLowerCase() === 'store') {
            sector = 'Retail';
            entity = 'Store';
            clients = 'Customers';
            action = 'browse products';
            focus = 'sales';
        } else {
            sector = 'Service';
            entity = 'Service';
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
        }

        const template = `Hello ${lead.business_name} 👋,
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

        return encodeURIComponent(template);
    };

    const renderLeads = (leads) => {
        if (!leads || leads.length === 0) {
            leadsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No new leads found. Try again later.</td></tr>';
            return;
        }

        leadsTableBody.innerHTML = '';
        leads.forEach(lead => {
            const tr = document.createElement('tr');

            const tdName = document.createElement('td');
            tdName.textContent = lead.business_name;
            tr.appendChild(tdName);

            const tdType = document.createElement('td');
            tdType.textContent = lead.type;
            tr.appendChild(tdType);

            const tdCity = document.createElement('td');
            tdCity.textContent = lead.city;
            tr.appendChild(tdCity);

            const tdPhone = document.createElement('td');
            tdPhone.textContent = lead.phone;
            tr.appendChild(tdPhone);

            const tdAction = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn-whatsapp';
            btn.setAttribute('data-id', lead.id);
            btn.setAttribute('data-phone', lead.phone);
            btn.setAttribute('data-name', lead.business_name);
            btn.setAttribute('data-type', lead.type);
            btn.textContent = 'Send WhatsApp';
            tdAction.appendChild(btn);
            tr.appendChild(tdAction);

            leadsTableBody.appendChild(tr);
        });
    };

    // Event delegation for WhatsApp button clicks
    leadsTableBody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone').replace(/\D/g, ''); // clean phone number
            const lead = {
                business_name: btn.getAttribute('data-name'),
                type: btn.getAttribute('data-type')
            };

            const message = generateWhatsAppMessage(lead);
            const waUrl = `https://wa.me/${phone}?text=${message}`;

            // Open WhatsApp synchronously to prevent popup blocker
            window.open(waUrl, '_blank');

            // Then tell backend to mark as contacted
            try {
                const res = await fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id })
                });

                if (res.ok) {
                    // Refresh data
                    fetchLeads();
                    fetchStats();
                }
            } catch (error) {
                console.error('Error marking lead as contacted:', error);
            }
        }
    });

    // Initial fetch
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);
});
