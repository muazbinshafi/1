// Fetch leads and update table
async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const data = await response.json();
        if (data.status === 'success') {
            updateTable(data.data);
        } else {
            console.error('Failed to fetch leads:', data.message);
        }
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

// Fetch stats and update analytics
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('total-leads').innerText = data.data.total;
            document.getElementById('contacted-leads').innerText = data.data.contacted;
            document.getElementById('new-leads').innerText = data.data.new;
        } else {
            console.error('Failed to fetch stats:', data.message);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Update table DOM
function updateTable(leads) {
    const tbody = document.getElementById('leads-body');
    tbody.innerHTML = '';

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No new leads found. Keep waiting for the scraper...</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.dataset.id = lead.id;

        // Dynamic messaging terms based on sector
        let entity = lead.type.toLowerCase();
        let clients = "clients";
        let action = "book appointments";
        let focus = "services";
        let sector = lead.type;

        if (lead.type === 'Clinic') {
            clients = "Patients";
            action = "book appointments";
            focus = "care";
        } else if (lead.type === 'Store') {
            clients = "Customers";
            action = "browse products";
            focus = "sales";
        } else if (lead.type === 'Service') {
            clients = "Clients";
            action = "book appointments";
            focus = "services";
        }

        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const currentDayIndex = new Date().getDay();
        const nextDayOfWeek = days[(currentDayIndex + 2) % 7]; // Propose a chat 2 days from now

        const message = `Hello ${lead.business_name} 👋,
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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${nextDayOfWeek}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

        // Format phone number to international format, remove spaces
        let phoneDigits = lead.phone.replace(/\D/g, '');
        // Make sure it starts with 92 for Pakistan
        if (phoneDigits.startsWith('0')) {
            phoneDigits = '92' + phoneDigits.substring(1);
        }

        const waUrl = `https://wa.me/${phoneDigits}?text=${encodeURIComponent(message)}`;

        tr.innerHTML = `
            <td>${lead.business_name}</td>
            <td>${lead.type}</td>
            <td>${lead.city}</td>
            <td>${lead.phone}</td>
            <td>
                <a href="${waUrl}" target="_blank" class="btn-whatsapp" data-action="contact">Send WhatsApp</a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Mark lead as contacted in database
async function markContacted(leadId) {
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ lead_id: leadId })
        });
        const data = await response.json();

        if (data.status === 'success') {
            // Remove the row from table
            const row = document.querySelector(`tr[data-id="${leadId}"]`);
            if (row) {
                row.remove();
            }
            // Update stats
            fetchStats();

            // Re-fetch leads to update table completely if needed
            // fetchLeads();
        } else {
            console.error('Failed to mark contacted:', data.message);
        }
    } catch (error) {
        console.error('Error marking contacted:', error);
    }
}

// Event Delegation for action buttons
document.getElementById('leads-table').addEventListener('click', function(e) {
    // If the clicked element or its parent is the Send WhatsApp button
    const target = e.target.closest('a[data-action="contact"]');
    if (target) {
        // Find lead ID from parent tr
        const tr = target.closest('tr');
        if (tr && tr.dataset.id) {
            const leadId = parseInt(tr.dataset.id, 10);

            // Asynchronously trigger backend update
            // URL will open in a new tab because target="_blank" is on the link, this happens synchronously
            markContacted(leadId);
        }
    }
});

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Set up polling interval every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);
});