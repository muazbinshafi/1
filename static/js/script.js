document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for "Send WhatsApp" button
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            // Optimistic UI update - remove instantly
            const row = btn.closest('tr');
            if (row) {
                row.remove();
            }

            // Trigger backend contact
            markContacted(id);

            // Construct Pitch
            const pitch = generatePitch(name, type);
            const encodedPitch = encodeURIComponent(pitch);

            // Standardize phone number for wa.me
            const cleanPhone = phone.replace(/[^0-9]/g, '');
            let waPhone = cleanPhone;
            // Assumes Pakistani number if it starts with 03
            if (waPhone.startsWith('03')) {
                waPhone = '92' + waPhone.substring(1);
            }

            const url = `https://wa.me/${waPhone}?text=${encodedPitch}`;
            window.open(url, '_blank');
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

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('stat-total').textContent = stats.total || 0;
        document.getElementById('stat-contacted').textContent = stats.contacted || 0;
        document.getElementById('stat-new').textContent = stats.new || 0;
    } catch (e) {
        console.error("Failed to fetch stats", e);
    }
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
                        data-id="${escapeHTML(lead.id)}"
                        data-name="${escapeHTML(lead.business_name)}"
                        data-type="${escapeHTML(lead.type)}"
                        data-phone="${escapeHTML(lead.phone)}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to fetch leads", e);
    }
}

async function markContacted(id) {
    try {
        await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: parseInt(id) })
        });
        fetchStats(); // Update stats explicitly after marking
    } catch (e) {
        console.error("Failed to mark contacted", e);
    }
}

function generatePitch(businessName, businessType) {
    const bTypeLow = businessType.toLowerCase();

    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    if (bTypeLow.includes('clinic') || bTypeLow.includes('health') || bTypeLow.includes('medical')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (bTypeLow.includes('service')) {
        sector = "Services";
        entity = "Service Provider";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    // Calculate chat day (+2 days)
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 2);
    const chatDay = days[targetDate.getDay()];

    return `Hello ${businessName} 👋,

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
}
