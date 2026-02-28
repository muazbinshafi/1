document.addEventListener('DOMContentLoaded', () => {
    const leadsBody = document.getElementById('leads-body');
    const totalLeadsEl = document.getElementById('total-leads');
    const contactedLeadsEl = document.getElementById('contacted-leads');
    const newLeadsEl = document.getElementById('new-leads');

    function fetchStats() {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                totalLeadsEl.textContent = data.total;
                contactedLeadsEl.textContent = data.contacted;
                newLeadsEl.textContent = data.new;
            });
    }

    function fetchLeads() {
        fetch('/api/leads')
            .then(res => res.json())
            .then(leads => {
                leadsBody.innerHTML = '';
                leads.forEach(lead => {
                    const tr = document.createElement('tr');
                    tr.dataset.id = lead.id;
                    tr.innerHTML = `
                        <td>${lead.business_name}</td>
                        <td>${lead.type}</td>
                        <td>${lead.city}</td>
                        <td>${lead.phone}</td>
                        <td>
                            <button class="btn-whatsapp" data-id="${lead.id}" data-name="${lead.business_name}" data-type="${lead.type}" data-phone="${lead.phone}">
                                Send WhatsApp
                            </button>
                        </td>
                    `;
                    leadsBody.appendChild(tr);
                });
            });
    }

    function generateMessage(name, type) {
        let sector = type;
        let entity = type.toLowerCase();
        let clients = '';
        let action = '';
        let focus = '';

        if (type.toLowerCase() === 'clinic') {
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
        } else if (type.toLowerCase() === 'store') {
            clients = 'Customers';
            action = 'browse products';
            focus = 'sales';
        } else {
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
        }

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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on Wednesday? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

        return encodeURIComponent(msg);
    }

    leadsBody.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.dataset.id;
            const name = btn.dataset.name;
            const type = btn.dataset.type;
            const phone = btn.dataset.phone.replace(/[^0-9]/g, '');

            const message = generateMessage(name, type);
            const waUrl = `https://wa.me/${phone}?text=${message}`;

            // Open WhatsApp in new tab
            window.open(waUrl, '_blank');

            // Mark as contacted on backend
            fetch(`/api/leads/${id}/contact`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Update UI immediately
                    const row = btn.closest('tr');
                    row.remove();
                    fetchStats();
                }
            });
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
