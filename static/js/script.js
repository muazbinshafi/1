document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll for updates every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            sendWhatsApp(leadId, phone, name, type, btn);
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

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            const loading = document.getElementById('loading');

            tbody.innerHTML = '';

            if (data.length === 0) {
                loading.textContent = 'No new leads found.';
                loading.classList.remove('hidden');
            } else {
                loading.classList.add('hidden');
                data.forEach(lead => {
                    const tr = document.createElement('tr');
                    tr.id = `lead-row-${lead.id}`;
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
            }
        })
        .catch(err => console.error('Error fetching leads:', err));
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-new').textContent = data.new;
            document.getElementById('stat-contacted').textContent = data.contacted;
        })
        .catch(err => console.error('Error fetching stats:', err));
}

function generateMessage(name, type) {
    let sector = "Business";
    let entity = "Business";
    let clients = "Customers";
    let action = "purchase";
    let focus = "operations";

    if (type.toLowerCase().includes('clinic') || type.toLowerCase() === 'healthcare') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "patient care";
    } else if (type.toLowerCase().includes('store') || type.toLowerCase() === 'retail') {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    } else if (type.toLowerCase().includes('service')) {
        sector = "Services";
        entity = "Service business";
        clients = "Clients";
        action = "book services";
        focus = "delivering quality service";
    }

    // Calculate a day 2 days from now
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const date = new Date();
    date.setDate(date.getDate() + 2);
    const chatDay = days[date.getDay()];

    const message = `Hello ${name} 👋,

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(message);
}

function sendWhatsApp(id, phone, name, type, btnElement) {
    // Optimistic UI update
    const row = document.getElementById(`lead-row-${id}`);
    if (row) {
        row.remove();
    }

    // Construct WhatsApp API URL
    // Ensure phone is formatted correctly for WhatsApp (needs country code, assuming Pakistan 92)
    let formattedPhone = phone.replace(/\D/g, '');
    if (formattedPhone.startsWith('03')) {
        formattedPhone = '92' + formattedPhone.substring(1);
    }

    const message = generateMessage(name, type);
    const whatsappUrl = `https://wa.me/${formattedPhone}?text=${message}`;

    // Open WhatsApp synchronously before the async fetch to prevent popup blockers
    window.open(whatsappUrl, '_blank');

    // Tell backend we contacted them
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: parseInt(id) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            fetchStats(); // Update counters
        } else {
            console.error('Failed to update lead status on server');
            // Optionally, we could put the row back here if it failed
        }
    })
    .catch(err => console.error('Error updating lead:', err));
}
