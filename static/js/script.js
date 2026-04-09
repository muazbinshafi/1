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
        if (e.target.closest('.btn-whatsapp')) {
            const btn = e.target.closest('.btn-whatsapp');
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            handleWhatsAppClick(leadId, phone, name, type, btn);
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

function sanitizePhone(phone) {
    return phone.replace(/[-\s]/g, '').replace(/^0/, '92');
}

function getNextChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = new Date();
    // Propose a chat 2 days from now
    const targetDay = new Date(today);
    targetDay.setDate(today.getDate() + 2);
    return days[targetDay.getDay()];
}

function generateWhatsAppMessage(name, type) {
    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    if (type.toLowerCase() === 'clinic') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase() === 'service') {
        sector = "Services";
        entity = "Service Provider";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const day = getNextChatDay();

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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${day}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(message);
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('stat-total').textContent = data.total;
        document.getElementById('stat-new').textContent = data.new;
        document.getElementById('stat-contacted').textContent = data.contacted;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        const tbody = document.getElementById('leads-body');
        tbody.innerHTML = '';

        if (leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No new leads found. System is collecting...</td></tr>';
            return;
        }

        leads.forEach(lead => {
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
                        <i class="fa-brands fa-whatsapp"></i> Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

function handleWhatsAppClick(leadId, phone, name, type, btnElement) {
    const cleanPhone = sanitizePhone(phone);
    const message = generateWhatsAppMessage(name, type);
    const whatsappUrl = `https://wa.me/${cleanPhone}?text=${message}`;

    // Open WhatsApp in new tab synchronously
    window.open(whatsappUrl, '_blank');

    // Optimistic UI update: hide the row instantly
    const row = document.getElementById(`lead-row-${leadId}`);
    if (row) {
        row.style.display = 'none';
    }

    // Call API to mark as contacted
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: leadId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update stats
            fetchStats();
        } else {
            // Revert UI if failed
            if (row) row.style.display = '';
            console.error('Failed to mark contacted');
        }
    })
    .catch(error => {
        // Revert UI if failed
        if (row) row.style.display = '';
        console.error('Error marking contacted:', error);
    });
}
