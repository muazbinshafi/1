document.addEventListener("DOMContentLoaded", () => {
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);
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

function fetchStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('stat-total').innerText = data.total;
            document.getElementById('stat-contacted').innerText = data.contacted;
            document.getElementById('stat-new').innerText = data.new;
        })
        .catch(error => console.error("Error fetching stats:", error));
}

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = '';

            data.forEach(lead => {
                const tr = document.createElement('tr');
                tr.setAttribute('data-id', lead.id);

                tr.innerHTML = `
                    <td>${escapeHTML(lead.business_name)}</td>
                    <td>${escapeHTML(lead.type)}</td>
                    <td>${escapeHTML(lead.city)}</td>
                    <td>${escapeHTML(lead.phone)}</td>
                    <td>
                        <button class="btn-whatsapp" data-id="${lead.id}" data-name="${escapeHTML(lead.business_name)}" data-type="${escapeHTML(lead.type)}" data-phone="${escapeHTML(lead.phone)}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => console.error("Error fetching leads:", error));
}

function getChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const date = new Date();
    date.setDate(date.getDate() + 2);
    return days[date.getDay()];
}

function generateWhatsAppMessage(businessName, type) {
    let clients, action, focus;

    if (type.toLowerCase() === 'clinic') {
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase() === 'store') {
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else {
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const day = getChatDay();

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

// Event delegation for WhatsApp buttons
document.getElementById('leads-body').addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-whatsapp')) {
        const id = e.target.getAttribute('data-id');
        const name = e.target.getAttribute('data-name');
        const type = e.target.getAttribute('data-type');
        let phone = e.target.getAttribute('data-phone');

        // Sanitize Pakistani phone number
        phone = phone.replace(/[-\s]/g, '').replace(/^0/, '');
        phone = '92' + phone; // Add country code

        const message = encodeURIComponent(generateWhatsAppMessage(name, type));
        const url = `https://wa.me/${phone}?text=${message}`;

        // Open WhatsApp link synchronously
        window.open(url, '_blank');

        // Optimistic UI update
        const tr = e.target.closest('tr');
        if (tr) {
            tr.remove();
        }

        // Call backend to mark as contacted
        fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        })
        .then(response => response.json())
        .then(() => {
            fetchStats(); // Update stats immediately
        })
        .catch(err => console.error('Error marking as contacted:', err));
    }
});
