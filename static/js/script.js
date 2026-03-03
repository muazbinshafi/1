document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData();

    // Poll every 30 seconds
    setInterval(fetchData, 30000);

    // Event delegation for the WhatsApp buttons
    const leadsBody = document.getElementById('leads-body');
    if (leadsBody) {
        leadsBody.addEventListener('click', handleWhatsAppClick);
    }
});

async function fetchData() {
    try {
        await Promise.all([fetchStats(), fetchLeads()]);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

async function fetchStats() {
    const response = await fetch('/api/stats');
    if (!response.ok) throw new Error('Failed to fetch stats');

    const stats = await response.json();

    document.getElementById('total-leads').textContent = stats.total;
    document.getElementById('contacted-leads').textContent = stats.contacted;
    document.getElementById('new-leads').textContent = stats.new;
}

async function fetchLeads() {
    const response = await fetch('/api/leads');
    if (!response.ok) throw new Error('Failed to fetch leads');

    const leads = await response.json();
    renderLeads(leads);
}

function renderLeads(leads) {
    const tbody = document.getElementById('leads-body');

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px;">No active leads available. Waiting for collector...</td></tr>';
        return;
    }

    tbody.innerHTML = leads.map(lead => `
        <tr data-id="${lead.id}">
            <td><strong>${escapeHtml(lead.business_name)}</strong></td>
            <td><span class="badge-type">${escapeHtml(lead.type)}</span></td>
            <td>${escapeHtml(lead.city)}</td>
            <td>${escapeHtml(lead.phone)}</td>
            <td>
                <button
                    class="btn-whatsapp"
                    data-id="${lead.id}"
                    data-name="${escapeHtml(lead.business_name)}"
                    data-type="${escapeHtml(lead.type)}"
                    data-phone="${escapeHtml(lead.phone)}">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.002.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.304-.058.116-.087.188-.173.289l-.26.304c-.087.086-.177.18-.076.354.101.174.449.741.964 1.201.666.598 1.236.786 1.41.874.174.086.275.072.376-.043l.42-.509c.115-.159.231-.13.39-.072.159.058 1.011.477 1.184.564.173.087.289.129.332.202.043.073.043.423-.101.827z"/>
                        <path d="M12.031 2C6.486 2 1.996 6.486 1.996 12.031c0 1.874.52 3.682 1.48 5.25L2 22l4.852-1.277c1.517.889 3.254 1.359 5.042 1.359h.005c5.543 0 10.035-4.488 10.035-10.034C21.933 6.486 17.443 2 12.031 2zm0 18.062h-.004c-1.572 0-3.11-.424-4.457-1.226l-.32-.19-3.313.869.885-3.23-.208-.332c-.881-1.401-1.346-3.02-1.346-4.686 0-4.428 3.6-8.028 8.031-8.028 4.428 0 8.03 3.602 8.03 8.03 0 4.43-3.6 8.031-8.03 8.031z"/>
                    </svg>
                    Send WhatsApp
                </button>
            </td>
        </tr>
    `).join('');
}

function handleWhatsAppClick(event) {
    const button = event.target.closest('.btn-whatsapp');
    if (!button) return;

    const id = button.getAttribute('data-id');
    const name = button.getAttribute('data-name');
    const type = button.getAttribute('data-type');
    let phone = button.getAttribute('data-phone');

    // Generate dynamic message
    const message = generateMessage(name, type);

    // Clean phone number for WhatsApp API
    phone = phone.replace(/[^\d+]/g, '');

    // 1. Synchronously open WhatsApp URL
    const waUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');

    // 2. Optimistically remove from UI
    const row = button.closest('tr');
    if (row) {
        row.style.opacity = '0.5';
        row.style.pointerEvents = 'none';

        // Let user see it fading for a moment before removing
        setTimeout(() => {
            row.remove();
            // Update stats optimistically
            const currentTotal = parseInt(document.getElementById('total-leads').textContent) || 0;
            const currentContacted = parseInt(document.getElementById('contacted-leads').textContent) || 0;
            const currentNew = parseInt(document.getElementById('new-leads').textContent) || 0;

            document.getElementById('contacted-leads').textContent = currentContacted + 1;
            document.getElementById('new-leads').textContent = Math.max(0, currentNew - 1);

            // Check if table empty
            const tbody = document.getElementById('leads-body');
            if (tbody && tbody.children.length === 0) {
                 tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 20px;">No active leads available. Waiting for collector...</td></tr>';
            }
        }, 800);
    }

    // 3. Mark as contacted in backend asynchronously
    fetch(`/api/mark_contacted/${id}`, { method: 'POST' })
        .then(res => {
            if (!res.ok) console.error("Failed to mark lead as contacted");
        })
        .catch(err => console.error("Error updating lead status:", err));
}

function generateMessage(businessName, type) {
    // Dynamic terminology map based on memory/prompt
    const termMap = {
        'Clinic': { sector: 'Healthcare', entity: 'Clinic', clients: 'Patients', action: 'book appointments', focus: 'care' },
        'Store': { sector: 'Retail', entity: 'Store', clients: 'Customers', action: 'buy products', focus: 'sales' },
        'Service': { sector: 'Services', entity: 'Service', clients: 'Clients', action: 'book appointments', focus: 'services' }
    };

    // Default to Service if unknown type
    const terms = termMap[type] || termMap['Service'];

    // Get current day of week for the meeting scheduling part
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    let targetDay = days[tomorrow.getDay() - 1]; // Convert 1-5 to Monday-Friday
    if (!targetDay) targetDay = 'Monday'; // If weekend, suggest Monday

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

I would love to discuss how we can help your ${terms.entity} thrive online. Are you available for a brief chat on ${targetDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
