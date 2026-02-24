document.addEventListener('DOMContentLoaded', () => {
    const leadsTableBody = document.querySelector('#leads-table tbody');
    const loadingDiv = document.getElementById('loading');
    const noLeadsDiv = document.getElementById('no-leads');

    // Stats elements
    const totalLeadsEl = document.getElementById('total-leads');
    const newLeadsEl = document.getElementById('new-leads');
    const contactedLeadsEl = document.getElementById('contacted-leads');

    // Mappings for dynamic content
    const typeMappings = {
        'Clinic': {
            sector: 'Healthcare',
            entity: 'Clinic',
            clients: 'Patients',
            action: 'book appointments',
            focus: 'care'
        },
        'Store': {
            sector: 'Retail',
            entity: 'Store',
            clients: 'Customers',
            action: 'browse products',
            focus: 'sales'
        },
        'Service': {
            sector: 'Service',
            entity: 'Service',
            clients: 'Clients',
            action: 'book appointments',
            focus: 'services'
        }
    };

    function getNextDayOfWeek() {
        const date = new Date();
        date.setDate(date.getDate() + 1);
        return date.toLocaleDateString('en-US', { weekday: 'long' });
    }

    function generateMessage(lead) {
        const mapping = typeMappings[lead.business_type] || typeMappings['Service'];
        const dayOfWeek = getNextDayOfWeek();

        return `Hello ${lead.name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${mapping.sector} sector. Your establishment caught our attention due to its strong community presence! 🌟
**The Digital Opportunity 📈**
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${mapping.entity} currently lacks a dedicated website.
**Your 24/7 Digital Partner 🕒**
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${mapping.clients} discover your services and ${mapping.action} while you focus on ${mapping.focus}. 💻✨
**Why Business Solutions?**
✅ **Competitive Advantage:** We specialize in creating platforms that outshine your competition.
🌐 **Digital Transformation:** We can elevate your ${mapping.entity} to become a recognized 'Digital Brand.'
🛠️ **Comprehensive Service:** From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${mapping.entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
    }

    function fetchLeads() {
        fetch('/api/leads')
            .then(response => response.json())
            .then(leads => {
                leadsTableBody.innerHTML = '';
                loadingDiv.style.display = 'none';

                if (leads.length === 0) {
                    noLeadsDiv.style.display = 'block';
                } else {
                    noLeadsDiv.style.display = 'none';
                    leads.forEach(lead => {
                        const row = document.createElement('tr');

                        // Action Button
                        const actionBtn = document.createElement('a');
                        actionBtn.href = '#';
                        actionBtn.className = 'action-btn';
                        actionBtn.textContent = 'Send WhatsApp';
                        actionBtn.onclick = (e) => {
                            e.preventDefault();
                            handleWhatsAppClick(lead);
                        };

                        row.innerHTML = `
                            <td>${lead.name}</td>
                            <td>${lead.business_type}</td>
                            <td>${lead.city}</td>
                            <td>${lead.phone}</td>
                            <td></td>
                        `;
                        row.cells[4].appendChild(actionBtn);
                        leadsTableBody.appendChild(row);
                    });
                }
            })
            .catch(error => console.error('Error fetching leads:', error));
    }

    function fetchStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(stats => {
                if (stats.total !== undefined) {
                    totalLeadsEl.textContent = stats.total;
                    newLeadsEl.textContent = stats.new;
                    contactedLeadsEl.textContent = stats.contacted;
                }
            })
            .catch(error => console.error('Error fetching stats:', error));
    }

    function handleWhatsAppClick(lead) {
        const message = generateMessage(lead);
        const encodedMessage = encodeURIComponent(message);
        const whatsappUrl = `https://wa.me/${lead.phone.replace(/[^0-9]/g, '')}?text=${encodedMessage}`;

        // Open WhatsApp
        window.open(whatsappUrl, '_blank');

        // Mark as contacted
        fetch(`/api/leads/${lead.id}/contacted`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Refresh data
                    fetchLeads();
                    fetchStats();
                }
            })
            .catch(error => console.error('Error marking contacted:', error));
    }

    // Initial load
    fetchLeads();
    fetchStats();

    // Poll every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);
});
