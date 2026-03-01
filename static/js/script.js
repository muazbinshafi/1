document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData();

    // Set up polling every 30 seconds
    setInterval(fetchData, 30000);

    // Refresh button listener
    document.getElementById('refresh-btn').addEventListener('click', fetchData);

    // Event delegation for "Send WhatsApp" buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('send-whatsapp') || e.target.closest('.send-whatsapp')) {
            const btn = e.target.classList.contains('send-whatsapp') ? e.target : e.target.closest('.send-whatsapp');

            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            handleWhatsAppClick(id, name, type, phone);
        }
    });
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

    const data = await response.json();

    document.getElementById('total-leads').textContent = data.total;
    document.getElementById('contacted-leads').textContent = data.contacted;
    document.getElementById('new-leads').textContent = data.new;
}

async function fetchLeads() {
    const response = await fetch('/api/leads');
    if (!response.ok) throw new Error('Failed to fetch leads');

    const leads = await response.json();
    renderLeadsTable(leads);
}

function renderLeadsTable(leads) {
    const tbody = document.getElementById('leads-body');

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666; padding: 2rem;">No new leads available. Collecting more...</td></tr>';
        return;
    }

    tbody.innerHTML = leads.map(lead => `
        <tr id="lead-${lead.id}">
            <td><strong>${escapeHtml(lead.business_name)}</strong></td>
            <td><span class="badge badge-${lead.type.toLowerCase()}">${escapeHtml(lead.type)}</span></td>
            <td>${escapeHtml(lead.city)}</td>
            <td>${escapeHtml(lead.phone)}</td>
            <td>
                <button
                    class="btn btn-primary send-whatsapp"
                    data-id="${lead.id}"
                    data-name="${escapeHtml(lead.business_name)}"
                    data-type="${escapeHtml(lead.type)}"
                    data-phone="${escapeHtml(lead.phone)}"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592zm3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.729.729 0 0 0-.529.247c-.182.198-.691.677-.691 1.654 0 .977.71 1.916.81 2.049.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z"/>
                    </svg>
                    Send WhatsApp
                </button>
            </td>
        </tr>
    `).join('');
}

async function handleWhatsAppClick(id, businessName, businessType, phone) {
    // Determine dynamic wording based on business type
    let sector, entity, clients, action, focus;

    switch (businessType.toLowerCase()) {
        case 'clinic':
            sector = 'Healthcare';
            entity = 'Clinic';
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
            break;
        case 'store':
        case 'retail':
            sector = 'Retail';
            entity = 'Store';
            clients = 'Customers';
            action = 'buy products';
            focus = 'sales';
            break;
        case 'service':
        default:
            sector = 'Services';
            entity = 'Service Business';
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
            break;
    }

    // Determine the day for the meeting (e.g., next Tuesday)
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = new Date();
    // Suggest a day 2 days from now, skip weekends
    let meetingDayDate = new Date(today);
    meetingDayDate.setDate(today.getDate() + 2);
    if (meetingDayDate.getDay() === 0) meetingDayDate.setDate(meetingDayDate.getDate() + 1); // If Sunday, move to Monday
    if (meetingDayDate.getDay() === 6) meetingDayDate.setDate(meetingDayDate.getDate() + 2); // If Saturday, move to Monday

    const meetingDay = days[meetingDayDate.getDay()];

    const messageTemplate = `Hello ${businessName} 👋,

This is MuazBinShafi, Owner of Business Solutions 🏢.

I hope this message finds you well. I'm reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${entity} currently lacks a dedicated website.

*Your 24/7 Digital Partner 🕒*
In today's digital world, a website acts as your most reliable assistant—it's available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${entity} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${meetingDay}? 📞

Best regards,

MuazBinShafi
Owner | Business Solutions 💼`;

    // 1. Open WhatsApp URL synchronously to avoid popup blockers
    // Format phone number: remove non-numeric chars except +
    const cleanPhone = phone.replace(/[^\d+]/g, '');
    const encodedMessage = encodeURIComponent(messageTemplate);
    const waUrl = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

    window.open(waUrl, '_blank');

    // 2. Mark as contacted in the backend
    try {
        const response = await fetch('/api/contacted', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        });

        if (response.ok) {
            // Remove row from UI immediately for better UX
            const row = document.getElementById(`lead-${id}`);
            if (row) row.remove();

            // Update stats immediately
            const totalEl = document.getElementById('total-leads');
            const contactedEl = document.getElementById('contacted-leads');
            const newEl = document.getElementById('new-leads');

            contactedEl.textContent = parseInt(contactedEl.textContent) + 1;
            newEl.textContent = Math.max(0, parseInt(newEl.textContent) - 1);

            // If table is empty now, show empty state
            const tbody = document.getElementById('leads-body');
            if (tbody.children.length === 0) {
                 tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666; padding: 2rem;">No new leads available. Collecting more...</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error marking lead as contacted:', error);
    }
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
         .toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
