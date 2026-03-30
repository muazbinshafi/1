document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll for updates every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event delegation for the WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            sendWhatsApp(id, name, type, phone);

            // Optimistic UI Update: remove the row instantly
            const row = btn.closest('tr');
            if (row) {
                row.remove();
            }
        }
    });
});

function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        const tbody = document.getElementById('leads-body');
        tbody.innerHTML = '';

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHTML(lead.business_name)}</td>
                <td>${escapeHTML(lead.type)}</td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp"
                        data-id="${lead.id}"
                        data-name="${escapeHTML(lead.business_name)}"
                        data-type="${escapeHTML(lead.type)}"
                        data-phone="${escapeHTML(lead.phone)}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('stat-total').textContent = stats.total;
        document.getElementById('stat-contacted').textContent = stats.contacted;
        document.getElementById('stat-new').textContent = stats.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

function getChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2);
    return days[d.getDay()];
}

function sendWhatsApp(id, businessName, businessType, phone) {
    // Determine terminology based on business type
    let sector = 'business';
    let entity = 'business';
    let clients = 'customers';
    let action = 'engage with your services';
    let focus = 'operations';

    const typeLower = businessType.toLowerCase();

    if (typeLower.includes('clinic') || typeLower.includes('health') || typeLower.includes('care')) {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (typeLower.includes('store') || typeLower.includes('retail') || typeLower.includes('shop')) {
        sector = 'Retail';
        entity = 'Store';
        clients = 'Customers';
        action = 'buy products';
        focus = 'sales';
    } else if (typeLower.includes('service') || typeLower.includes('provider')) {
        sector = 'Services';
        entity = 'Service';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const chatDay = getChatDay();

    // Construct the message
    const message = `Hello ${businessName} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    const encodedMessage = encodeURIComponent(message);

    // Clean phone number: remove non-numeric characters except +
    const cleanPhone = phone.replace(/[^\d+]/g, '');
    const finalPhone = cleanPhone.startsWith('0') ? '92' + cleanPhone.substring(1) : cleanPhone;

    const whatsappUrl = `https://wa.me/${finalPhone}?text=${encodedMessage}`;

    // Open WhatsApp synchronously before the async fetch to prevent popup blockers
    window.open(whatsappUrl, '_blank');

    // Mark as contacted in the backend
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Re-fetch stats to reflect the changes
            fetchStats();
        }
    })
    .catch(error => {
        console.error('Error marking as contacted:', error);
    });
}
