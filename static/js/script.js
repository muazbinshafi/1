document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll for updates every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const businessName = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            handleWhatsAppClick(leadId, businessName, type, phone, btn.closest('tr'));
        }
    });
});

function escapeHTML(str) {
    const p = document.createElement('p');
    p.appendChild(document.createTextNode(str));
    return p.innerHTML;
}

function fetchStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-leads').textContent = data.total;
            document.getElementById('new-leads').textContent = data.new;
            document.getElementById('contacted-leads').textContent = data.contacted;
        })
        .catch(err => console.error('Error fetching stats:', err));
}

function fetchLeads() {
    fetch('/api/leads')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = '';
            data.forEach(lead => {
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
        })
        .catch(err => console.error('Error fetching leads:', err));
}

function sanitizePhone(phone) {
    // Remove hyphens, spaces, and specifically the leading zero
    return "92" + phone.replace(/[-\s]/g, '').replace(/^0/, '');
}

function getMeetingDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const date = new Date();
    date.setDate(date.getDate() + 2);
    return days[date.getDay()];
}

function generateMessage(businessName, type) {
    let sector = type;
    let entity = type;
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";

    if (type.toLowerCase() === 'clinic') {
        sector = "Healthcare";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase() === 'store') {
        sector = "Retail";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else if (type.toLowerCase() === 'service') {
        sector = "Services";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const day = getMeetingDay();

    return `Hello ${businessName} 👋,

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function handleWhatsAppClick(leadId, businessName, type, phone, rowElement) {
    const formattedPhone = sanitizePhone(phone);
    const message = encodeURIComponent(generateMessage(businessName, type));
    const url = `https://wa.me/${formattedPhone}?text=${message}`;

    // Open WhatsApp synchronously to avoid popup blockers
    window.open(url, '_blank');

    // Optimistic UI update
    rowElement.remove();

    // Update backend
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: leadId }),
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            fetchStats(); // Update stats after marking as contacted
        }
    })
    .catch(err => console.error('Error marking as contacted:', err));
}
