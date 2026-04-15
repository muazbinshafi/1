document.addEventListener('DOMContentLoaded', () => {
    fetchStatsAndLeads();

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const button = e.target;
            const leadId = button.getAttribute('data-id');
            const phone = button.getAttribute('data-phone');
            const name = button.getAttribute('data-name');
            const type = button.getAttribute('data-type');

            // 1. Generate message and open WhatsApp synchronously to prevent popup blocking
            const message = generateMessage(name, type);
            const sanitizedPhone = sanitizePhone(phone);
            const waUrl = `https://wa.me/92${sanitizedPhone}?text=${encodeURIComponent(message)}`;
            window.open(waUrl, '_blank');

            // 2. Optimistic UI Update: remove row instantly
            const row = button.closest('tr');
            if (row) {
                row.remove();
            }

            // 3. Backend API call to mark as contacted
            markLeadContacted(leadId);
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
    // Strip hyphens, spaces, and specifically the leading zero
    return phone.replace(/[-\s]/g, '').replace(/^0/, '');
}

function generateMessage(businessName, type) {
    let sector = "General";
    let entity = "Business";
    let clients = "Clients";
    let action = "utilize your services";
    let focus = "operations";

    const typeLower = type.toLowerCase();

    if (typeLower.includes("clinic")) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower.includes("store")) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    } else if (typeLower.includes("service")) {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    // Calculate chat day (2 days from now)
    const chatDate = new Date();
    chatDate.setDate(chatDate.getDate() + 2);
    const dayOfWeek = chatDate.toLocaleDateString('en-US', { weekday: 'long' });

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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

function fetchStatsAndLeads() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Update stats
            document.getElementById('total-leads').textContent = data.total;
            document.getElementById('contacted-leads').textContent = data.contacted;
            document.getElementById('new-leads').textContent = data.new;

            // Populate table
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = ''; // Clear existing

            data.leads.forEach(lead => {
                const tr = document.createElement('tr');
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
        })
        .catch(err => console.error('Error fetching data:', err));
}

function markLeadContacted(leadId) {
    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: leadId }),
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success') {
            // Re-fetch to update numbers
            fetchStatsAndLeads();
        }
    })
    .catch(err => console.error('Error marking contacted:', err));
}
