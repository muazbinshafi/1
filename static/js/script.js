document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
});

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const data = await response.json();

        if (data.error) {
            console.error('Error fetching leads:', data.error);
            return;
        }

        updateStats(data.stats);
        renderTable(data.leads);
    } catch (error) {
        console.error('Network error fetching leads:', error);
    }
}

function updateStats(stats) {
    document.getElementById('total-leads-count').textContent = stats.total;
    document.getElementById('pending-leads-count').textContent = stats.pending;
    document.getElementById('contacted-leads-count').textContent = stats.contacted;
}

function renderTable(leads) {
    const tbody = document.getElementById('leads-body');
    tbody.innerHTML = '';

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No pending leads available. Background scraper is running...</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.dataset.id = lead.id;

        tr.innerHTML = `
            <td>${escapeHTML(lead.name)}</td>
            <td>${escapeHTML(lead.type)}</td>
            <td>${escapeHTML(lead.city)}</td>
            <td>${escapeHTML(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp" onclick="sendWhatsApp(${lead.id}, '${escapeHTML(lead.name)}', '${escapeHTML(lead.type)}', '${escapeHTML(lead.phone)}')">
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function generateMessage(businessName, type) {
    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    if (type.toLowerCase() === 'clinic') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase() === 'service') {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = new Date();
    const chatDay = days[(today.getDay() + 2) % 7];

    return `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟
*The Digital Opportunity* 📈
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entity} currently lacks a dedicated website.
*Your 24/7 Digital Partner* 🕒
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨
*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${entity} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function sendWhatsApp(id, name, type, phone) {
    // 1. Prepare data
    const message = generateMessage(name, type);
    const cleanPhone = phone.replace(/[-\s]/g, '').replace(/^0/, '92');
    const url = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;

    // 2. Open WhatsApp immediately (sync) to avoid popup blockers
    window.open(url, '_blank');

    // 3. Optimistic UI update
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (row) {
        row.remove();
    }

    // Update stats optimistically
    const pendingCount = document.getElementById('pending-leads-count');
    const contactedCount = document.getElementById('contacted-leads-count');

    if (pendingCount && pendingCount.textContent > 0) {
        pendingCount.textContent = parseInt(pendingCount.textContent) - 1;
    }
    if (contactedCount) {
        contactedCount.textContent = parseInt(contactedCount.textContent) + 1;
    }

    // 4. Update backend
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Failed to update lead status:', data.error);
            // Optionally, we could revert the optimistic update here if needed.
        }
    })
    .catch(error => {
        console.error('Network error updating lead status:', error);
    });
}
