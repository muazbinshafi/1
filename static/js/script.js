document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Refresh every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            sendWhatsApp(leadId, phone, name, type, btn.closest('tr'));
        }
    });
});

function escapeHtml(unsafe) {
    return (unsafe || '').toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function cleanPhoneNumber(phone) {
    if (!phone) return '';
    return phone.replace(/[-\s]/g, '').replace(/^0/, '');
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('total-leads').textContent = stats.total;
        document.getElementById('new-leads').textContent = stats.new;
        document.getElementById('contacted-leads').textContent = stats.contacted;
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

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${escapeHtml(lead.business_name)}</td>
                <td>${escapeHtml(lead.type)}</td>
                <td>${escapeHtml(lead.city)}</td>
                <td>${escapeHtml(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp"
                        data-id="${lead.id}"
                        data-phone="${escapeHtml(lead.phone)}"
                        data-name="${escapeHtml(lead.business_name)}"
                        data-type="${escapeHtml(lead.type)}">
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

function getMeetingDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const date = new Date();
    date.setDate(date.getDate() + 2); // 2 days from now
    return days[date.getDay()];
}

function generateMessage(name, type) {
    const meetingDay = getMeetingDay();
    let sector = "Business";
    let entity = "Business";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    const typeLower = (type || '').toLowerCase();
    if (typeLower.includes("clinic")) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower.includes("store") || typeLower.includes("retail")) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else if (typeLower.includes("service")) {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${meetingDay}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(message);
}

async function sendWhatsApp(id, phone, name, type, rowElement) {
    const cleanPhone = cleanPhoneNumber(phone);
    if (!cleanPhone) {
        alert("Invalid phone number");
        return;
    }

    const message = generateMessage(name, type);
    // WhatsApp requires country code, assume +92 for Pakistan
    const waUrl = `https://wa.me/92${cleanPhone}?text=${message}`;

    // Open synchronously to avoid popup blockers
    window.open(waUrl, '_blank');

    // Optimistic UI update
    rowElement.remove();

    // Update count immediately in UI
    const newLeadsEl = document.getElementById('new-leads');
    const contactedLeadsEl = document.getElementById('contacted-leads');
    if(newLeadsEl && contactedLeadsEl) {
        newLeadsEl.textContent = Math.max(0, parseInt(newLeadsEl.textContent || '0') - 1);
        contactedLeadsEl.textContent = parseInt(contactedLeadsEl.textContent || '0') + 1;
    }

    // Call backend
    try {
        await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: parseInt(id) })
        });

        // Ensure stats and leads are perfectly synced with backend
        fetchStats();
    } catch (error) {
        console.error('Error updating contact status:', error);
        // Refresh to get back correct state if failed
        fetchLeads();
        fetchStats();
    }
}