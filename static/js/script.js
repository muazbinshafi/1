document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            sendWhatsApp(id, phone, name, type, btn.closest('tr'));
        }
    });
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

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-leads').innerText = data.total;
            document.getElementById('contacted-leads').innerText = data.contacted;
            document.getElementById('new-leads').innerText = data.new;
        });
}

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(leads => {
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
                            data-phone="${escapeHTML(lead.phone)}"
                            data-name="${escapeHTML(lead.business_name)}"
                            data-type="${escapeHTML(lead.type)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
}

function getNextDayOfWeek() {
    const d = new Date();
    d.setDate(d.getDate() + 2); // Dynamically propose a chat 2 days from now
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[d.getDay()];
}

function generateMessage(name, type) {
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

    const day = getNextDayOfWeek();

    return `Hello ${name} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function sendWhatsApp(id, rawPhone, name, type, rowElement) {
    // Sanitize phone number according to memory guidelines
    const sanitizedPhone = '92' + rawPhone.replace(/[-\s]/g, '').replace(/^0/, '');
    const message = encodeURIComponent(generateMessage(name, type));
    const url = `https://wa.me/${sanitizedPhone}?text=${message}`;

    // Open WhatsApp synchronously before fetching to prevent popup blockers
    window.open(url, '_blank');

    // Optimistic UI Update
    rowElement.remove();

    // Mark as contacted in the backend
    fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
    }).then(() => {
        fetchStats();
    });
}
