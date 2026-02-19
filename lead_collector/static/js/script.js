document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchAnalytics();

    document.getElementById('collect-btn').addEventListener('click', async () => {
        const btn = document.getElementById('collect-btn');
        btn.disabled = true;
        btn.textContent = 'Collecting...';
        try {
            const response = await fetch('/api/collect', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                alert(`Collected ${data.count} new leads!`);
                fetchLeads();
                fetchAnalytics();
            }
        } catch (error) {
            console.error('Error collecting leads:', error);
            alert('Failed to collect leads.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Collect More Leads';
        }
    });
});

async function fetchLeads() {
    const tableBody = document.querySelector('#leads-table tbody');
    const loading = document.getElementById('loading');
    const emptyState = document.getElementById('empty-state');

    tableBody.innerHTML = '';
    loading.classList.remove('hidden');
    emptyState.classList.add('hidden');

    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        loading.classList.add('hidden');

        if (leads.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }

        leads.forEach(lead => {
            const row = document.createElement('tr');

            // Create cells manually to avoid inline onclick issues
            const nameCell = document.createElement('td');
            nameCell.textContent = lead.name;

            const typeCell = document.createElement('td');
            typeCell.innerHTML = `<span class="badge badge-${lead.type.toLowerCase()}">${lead.type}</span>`;

            const cityCell = document.createElement('td');
            cityCell.textContent = lead.city;

            const phoneCell = document.createElement('td');
            phoneCell.textContent = lead.phone;

            const actionCell = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn btn-whatsapp';
            btn.innerHTML = `Send WhatsApp <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.592 2.654-.698c1.005.549 1.956.816 3.036.817 3.193 0 5.776-2.587 5.776-5.766 0-1.545-.601-2.997-1.694-4.089-1.094-1.094-2.544-1.695-4.088-1.695zm.022 10.18c-1.082 0-1.896-.285-2.866-.826l-.206-.115-1.536.403.411-1.498-.135-.216c-.663-1.055-.945-1.78-.944-2.731.001-2.457 1.996-4.453 4.453-4.453 1.189 0 2.308.463 3.149 1.304 1.737 1.736 1.736 4.555 0 6.292-.841.84-1.96 1.304-3.149 1.304z"/></svg>`;
            btn.onclick = () => handleWhatsAppClick(lead.id, lead.name, lead.type, lead.phone);
            actionCell.appendChild(btn);

            row.appendChild(nameCell);
            row.appendChild(typeCell);
            row.appendChild(cityCell);
            row.appendChild(phoneCell);
            row.appendChild(actionCell);

            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error('Error fetching leads:', error);
        loading.textContent = 'Error loading leads.';
    }
}

async function fetchAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        document.getElementById('new-leads-count').textContent = data.new_leads || 0;
        document.getElementById('contacted-leads-count').textContent = data.contacted_leads || 0;
    } catch (error) {
        console.error('Error fetching analytics:', error);
    }
}

function handleWhatsAppClick(id, name, type, phone) {
    const message = generateWhatsAppMessage(name, type);
    const encodedMessage = encodeURIComponent(message);
    const url = `https://wa.me/${phone.replace(/\s+/g, '').replace('+', '')}?text=${encodedMessage}`;

    // Open WhatsApp in new tab
    window.open(url, '_blank');

    // Mark as contacted (soft delete)
    markAsContacted(id);
}

async function markAsContacted(id) {
    try {
        await fetch(`/api/contact/${id}`, { method: 'POST' });
        // Refresh leads and analytics
        fetchLeads();
        fetchAnalytics();
    } catch (error) {
        console.error('Error marking lead as contacted:', error);
    }
}

function generateWhatsAppMessage(businessName, type) {
    let sector, entity, clients, action, focus;

    switch (type) {
        case 'Clinic':
            sector = 'Healthcare';
            entity = 'Clinic';
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
            break;
        case 'Store':
            sector = 'Retail';
            entity = 'Store';
            clients = 'Customers';
            action = 'browse products';
            focus = 'sales';
            break;
        case 'Service':
        default:
            sector = 'Services';
            entity = 'Service Provider';
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
            break;
    }

    // Get next day for "Day of the Week"
    const date = new Date();
    date.setDate(date.getDate() + 1);
    const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' });

    return `Hello ${businessName} 👋,
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
}
