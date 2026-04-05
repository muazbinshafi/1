document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const row = btn.closest('tr');

            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            // Clean phone number (remove spaces, hyphens)
            const cleanPhone = '92' + phone.replace(/[-\s]/g, '').replace(/^0/, '').substring(0, 10);

            const message = generatePitch(name, type);
            const url = `https://api.whatsapp.com/send?phone=${cleanPhone}&text=${encodeURIComponent(message)}`;

            // Open WhatsApp immediately to avoid popup blockers
            window.open(url, '_blank');

            // Optimistically remove row
            row.remove();

            // Update backend
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id: id })
            }).then(() => fetchStats());
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
        }[tag])
    );
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
                            data-name="${escapeHTML(lead.business_name)}"
                            data-type="${escapeHTML(lead.type)}"
                            data-phone="${escapeHTML(lead.phone)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        });
}

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            document.getElementById('stat-total').textContent = stats.total;
            document.getElementById('stat-contacted').textContent = stats.contacted;
            document.getElementById('stat-new').textContent = stats.new;
        });
}

function generatePitch(businessName, type) {
    let clients, action, focus;

    type = type.toLowerCase();

    if (type === 'clinic') {
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type === 'store') {
        clients = 'Customers';
        action = 'browse products';
        focus = 'sales';
    } else {
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    const day = getDayOfWeekInTwoDays();

    return `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${type} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${type} currently lacks a dedicated website.

*Your 24/7 Digital Partner 🕒*
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${type} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${type} thrive online. Are you available for a brief chat on ${day}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function getDayOfWeekInTwoDays() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const date = new Date();
    date.setDate(date.getDate() + 2);
    return days[date.getDay()];
}
