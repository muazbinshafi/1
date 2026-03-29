document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Auto refresh data every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            // Optimistic UI update: hide row immediately
            const row = btn.closest('tr');
            row.style.display = 'none';

            // Generate message and URL
            const message = generateMessage(name, type);
            const encodedMessage = encodeURIComponent(message);
            // Assuming phone is already in international format from backend
            const cleanPhone = phone.replace(/[^0-9+]/g, '');
            const whatsappUrl = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

            // Open WhatsApp
            window.open(whatsappUrl, '_blank');

            // Mark as contacted in backend
            markContacted(leadId);
        }
    });
});

function escapeHTML(str) {
    if (!str) return '';
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

function fetchStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            if (data.error) return console.error(data.error);
            document.getElementById('stat-total').textContent = data.total || 0;
            document.getElementById('stat-contacted').textContent = data.contacted || 0;
            document.getElementById('stat-new').textContent = data.new || 0;
        })
        .catch(err => console.error('Error fetching stats:', err));
}

function fetchLeads() {
    const loading = document.getElementById('loading');
    const tbody = document.getElementById('leads-body');

    // Only show loading if table is empty
    if (tbody.children.length === 0) {
        loading.style.display = 'block';
    }

    fetch('/api/leads')
        .then(res => res.json())
        .then(data => {
            loading.style.display = 'none';
            if (data.error) return console.error(data.error);

            tbody.innerHTML = '';

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No uncontacted leads found. Waiting for scraper...</td></tr>';
                return;
            }

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
        .catch(err => {
            loading.style.display = 'none';
            console.error('Error fetching leads:', err);
        });
}

function markContacted(id) {
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success) {
            fetchStats(); // Update stats immediately
        }
    })
    .catch(err => console.error('Error marking contacted:', err));
}

function generateMessage(businessName, businessType) {
    const typeLower = businessType.toLowerCase();

    let sector = "Business";
    let entity = "Business";
    let clients = "Clients";
    let action = "discover your services";
    let focus = "daily operations";

    if (typeLower.includes("clinic") || typeLower.includes("health") || typeLower.includes("medical")) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower.includes("store") || typeLower.includes("retail") || typeLower.includes("mart") || typeLower.includes("shop")) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else if (typeLower.includes("service") || typeLower.includes("repair") || typeLower.includes("plumber") || typeLower.includes("electrician")) {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    // Calculate a day for the chat (e.g., 2 days from now)
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 2);
    const chatDay = days[d.getDay()];

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}
