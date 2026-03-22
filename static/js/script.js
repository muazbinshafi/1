document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for "Send WhatsApp" buttons
    document.getElementById('leads-body').addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' && e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const leadId = btn.getAttribute('data-id');
            const phone = btn.getAttribute('data-phone');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');

            sendWhatsApp(leadId, phone, name, type, btn);
        }
    });
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        document.getElementById('stat-total').innerText = stats.total;
        document.getElementById('stat-contacted').innerText = stats.contacted;
        document.getElementById('stat-new').innerText = stats.new;
    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        const tbody = document.getElementById('leads-body');

        tbody.innerHTML = ''; // Clear existing

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-row-id', lead.id);

            const tdName = document.createElement('td');
            tdName.textContent = lead.business_name;
            tr.appendChild(tdName);

            const tdType = document.createElement('td');
            tdType.textContent = lead.type;
            tr.appendChild(tdType);

            const tdCity = document.createElement('td');
            tdCity.textContent = lead.city;
            tr.appendChild(tdCity);

            const tdPhone = document.createElement('td');
            tdPhone.textContent = lead.phone;
            tr.appendChild(tdPhone);

            const tdAction = document.createElement('td');
            const btn = document.createElement('button');
            btn.className = 'btn-whatsapp';
            btn.setAttribute('data-id', lead.id);
            btn.setAttribute('data-phone', lead.phone);
            btn.setAttribute('data-name', lead.business_name);
            btn.setAttribute('data-type', lead.type);
            btn.textContent = 'Send WhatsApp';
            tdAction.appendChild(btn);
            tr.appendChild(tdAction);

            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error fetching leads:", error);
    }
}

function getPitchTemplate(name, type) {
    let sector = type;
    let entity = type;
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";

    if (type.toLowerCase() === 'clinic') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type.toLowerCase() === 'store' || type.toLowerCase() === 'retail') {
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

    const today = new Date();
    today.setDate(today.getDate() + 2);
    const options = { weekday: 'long' };
    const chatDay = today.toLocaleDateString('en-US', options);

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${chatDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    return encodeURIComponent(message);
}

function sendWhatsApp(id, phone, name, type, btnElement) {
    const message = getPitchTemplate(name, type);
    // Remove '+' and spaces for the wa.me link
    const cleanPhone = phone.replace(/[^0-9]/g, '');
    const waUrl = `https://wa.me/${cleanPhone}?text=${message}`;

    // Open synchronously to avoid popup blockers
    window.open(waUrl, '_blank');

    // Optimistically update UI
    const row = btnElement.closest('tr');
    if (row) row.remove();

    // Call API to mark as contacted
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            fetchStats(); // Update stats
        }
    })
    .catch(error => console.error("Error marking lead contacted:", error));
}
