const leadsBody = document.getElementById('leads-body');
const loadingIndicator = document.getElementById('loading');
const totalLeadsEl = document.getElementById('total-leads');
const newLeadsEl = document.getElementById('new-leads');
const contactedLeadsEl = document.getElementById('contacted-leads');

// HTML Escape function to prevent XSS
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag])
    );
}

function getMeetingDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2); // Propose chat day 2 days from now
    return days[d.getDay()];
}

function generateMessage(lead) {
    const type = lead.type;
    let entity, clients, action, focus, sector;

    if (type === 'Clinic') {
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
        sector = 'Healthcare';
    } else if (type === 'Store') {
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

    const meetingDay = getMeetingDay();

    return `Hello ${lead.business_name} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${meetingDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function renderLeads(leads) {
    leadsBody.innerHTML = '';

    if (leads.length === 0) {
        leadsBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No new leads available. Background collection may be running.</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const row = document.createElement('tr');
        row.dataset.id = lead.id;

        row.innerHTML = `
            <td>${escapeHTML(lead.business_name)}</td>
            <td>${escapeHTML(lead.type)}</td>
            <td>${escapeHTML(lead.city)}</td>
            <td>${escapeHTML(lead.phone)}</td>
            <td>
                <button class="whatsapp-btn" data-lead='${JSON.stringify(lead).replace(/'/g, "&apos;")}'>Send WhatsApp</button>
            </td>
        `;
        leadsBody.appendChild(row);
    });
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        loadingIndicator.style.display = 'none';
        renderLeads(leads);
    } catch (error) {
        console.error('Error fetching leads:', error);
        loadingIndicator.innerText = 'Error loading leads. Retrying...';
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        totalLeadsEl.innerText = stats.total;
        newLeadsEl.innerText = stats.new;
        contactedLeadsEl.innerText = stats.contacted;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function markContacted(leadId) {
    try {
        await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: leadId })
        });
        // Refresh stats after marking as contacted
        fetchStats();
    } catch (error) {
        console.error('Error marking lead as contacted:', error);
    }
}

// Event Delegation for WhatsApp buttons
leadsBody.addEventListener('click', (e) => {
    if (e.target.classList.contains('whatsapp-btn')) {
        const btn = e.target;
        const lead = JSON.parse(btn.dataset.lead);

        // Sanitize phone number correctly (remove hyphens, spaces, and specifically leading zero)
        const sanitizedPhone = lead.phone.replace(/[-\s]/g, '').replace(/^0/, '');
        const internationalPhone = `92${sanitizedPhone}`;

        const message = encodeURIComponent(generateMessage(lead));
        const whatsappUrl = `https://wa.me/${internationalPhone}?text=${message}`;

        // Open WhatsApp URL synchronously to avoid popup blockers
        window.open(whatsappUrl, '_blank');

        // Optimistic UI update: remove row instantly
        const row = btn.closest('tr');
        if (row) row.remove();

        // Update backend asynchronously
        markContacted(lead.id);
    }
});

// Initial load
fetchLeads();
fetchStats();

// Poll every 30 seconds
setInterval(() => {
    fetchLeads();
    fetchStats();
}, 30000);
