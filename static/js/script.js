document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
});

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        document.getElementById('total-leads').textContent = leads.length;

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
                    <button class="btn-whatsapp" data-id="${lead.id}"
                            data-name="${escapeHTML(lead.business_name)}"
                            data-type="${escapeHTML(lead.type)}"
                            data-phone="${escapeHTML(lead.phone)}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        attachButtonListeners();
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

function attachButtonListeners() {
    const buttons = document.querySelectorAll('.btn-whatsapp');
    buttons.forEach(btn => {
        btn.addEventListener('click', handleWhatsAppClick);
    });
}

function handleWhatsAppClick(event) {
    const btn = event.target;
    const id = btn.getAttribute('data-id');
    const name = btn.getAttribute('data-name');
    const type = btn.getAttribute('data-type');
    let phone = btn.getAttribute('data-phone');

    // Format phone number to WhatsApp style (e.g., replace 0 with 92)
    phone = phone.replace(/[-\s]/g, '').replace(/^0/, '92');

    // Determine dynamic wording
    let sector = type;
    let entity = type;
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";

    if (type.toLowerCase().includes('clinic')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase().includes('retail')) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    // Get a dynamic day (e.g., 2 days from now)
    const date = new Date();
    date.setDate(date.getDate() + 2);
    const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' });

    // Construct the pitch
    const message = `Hello ${name} 👋,
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

    const encodedMessage = encodeURIComponent(message);
    const waUrl = `https://wa.me/${phone}?text=${encodedMessage}`;

    // Open WA synchronously
    window.open(waUrl, '_blank');

    // Optimistically remove row
    const row = btn.closest('tr');
    if (row) {
        row.remove();
        const countSpan = document.getElementById('total-leads');
        countSpan.textContent = parseInt(countSpan.textContent) - 1;
    }

    // Update backend asynchronously
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id })
    }).catch(err => console.error('Failed to update lead status:', err));
}

function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}