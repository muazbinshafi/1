document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    document.getElementById('collectBtn').addEventListener('click', triggerCollection);
});

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(leads => {
            renderTable(leads);
            updateAnalytics(leads.length);
        })
        .catch(err => console.error('Error fetching leads:', err));
}

function renderTable(leads) {
    const tbody = document.querySelector('#leadsTable tbody');
    tbody.innerHTML = '';

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No new leads found. Click "Collect Leads" to find more.</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');

        const nameTd = document.createElement('td');
        nameTd.textContent = lead.name;
        tr.appendChild(nameTd);

        const typeTd = document.createElement('td');
        typeTd.textContent = lead.type;
        tr.appendChild(typeTd);

        const cityTd = document.createElement('td');
        cityTd.textContent = lead.city;
        tr.appendChild(cityTd);

        const phoneTd = document.createElement('td');
        phoneTd.textContent = lead.phone;
        tr.appendChild(phoneTd);

        const actionTd = document.createElement('td');
        const btn = document.createElement('a');
        btn.href = "#";
        btn.className = "whatsapp-btn";
        btn.innerHTML = '<span>📱</span> Send WhatsApp';
        btn.addEventListener('click', (e) => handleWhatsAppClick(e, lead));
        actionTd.appendChild(btn);
        tr.appendChild(actionTd);

        tbody.appendChild(tr);
    });
}

function updateAnalytics(total) {
    document.getElementById('totalLeads').innerText = total;
    // Contacted count would require fetching another endpoint or local storage tracking
}

function triggerCollection() {
    const btn = document.getElementById('collectBtn');
    const status = document.getElementById('status');

    btn.disabled = true;
    btn.innerText = 'Collecting...';
    status.innerText = 'Please wait, searching for businesses...';

    fetch('/api/collect', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                status.innerText = 'Collection complete!';
                fetchLeads();
            } else {
                status.innerText = 'Error: ' + data.error;
            }
        })
        .catch(err => {
            status.innerText = 'Error triggering collection.';
            console.error(err);
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<span class="icon">🔍</span> Collect Leads';
            setTimeout(() => status.innerText = '', 3000);
        });
}

function handleWhatsAppClick(event, lead) {
    event.preventDefault();

    const message = generateMessage(lead);
    const url = `https://wa.me/${lead.phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(message)}`;

    // Open in new tab
    window.open(url, '_blank');

    // Mark as contacted
    fetch(`/api/leads/${lead.id}/contacted`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Remove row or refresh
                fetchLeads();

                // Increment local contacted counter for demo
                const contactedElem = document.getElementById('contactedToday');
                let count = parseInt(contactedElem.innerText);
                contactedElem.innerText = count + 1;
            }
        })
        .catch(err => console.error('Error marking contacted:', err));
}

function generateMessage(lead) {
    const typeMap = {
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
            action: 'buy products',
            focus: 'sales'
        },
        'Service': {
            sector: 'Services',
            entity: 'Service Provider',
            clients: 'Clients',
            action: 'book appointments',
            focus: 'services'
        }
    };

    // Default to Service if type unknown
    const map = typeMap[lead.type] || typeMap['Service'];

    const dayOfWeek = new Date().toLocaleDateString('en-US', { weekday: 'long' });

    return `Hello ${lead.name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${map.sector} sector. Your establishment caught our attention due to its strong community presence! 🌟
**The Digital Opportunity 📈**
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${map.entity} currently lacks a dedicated website.
**Your 24/7 Digital Partner 🕒**
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${map.clients} discover your services and ${map.action} while you focus on ${map.focus}. 💻✨
**Why Business Solutions?**
✅ **Competitive Advantage:** We specialize in creating platforms that outshine your competition.
🌐 **Digital Transformation:** We can elevate your ${map.entity} to become a recognized 'Digital Brand.'
🛠️ **Comprehensive Service:** From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${map.entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}
