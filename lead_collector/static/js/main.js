document.addEventListener('DOMContentLoaded', function() {
    fetchLeads();
    // updateStats(); // Not implemented
});

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(leads => {
            const tbody = document.getElementById('leads-table-body');
            tbody.innerHTML = '';
            const totalLeadsEl = document.getElementById('total-leads-count');
            if(totalLeadsEl) totalLeadsEl.textContent = leads.length;

            if (leads.length === 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="5" class="text-center text-muted">No new leads found. Trigger collection to find more.</td>';
                tbody.appendChild(tr);
                return;
            }

            leads.forEach(lead => {
                const tr = document.createElement('tr');

                // Name
                const tdName = document.createElement('td');
                tdName.innerHTML = `<strong>${lead.name}</strong>`;
                tr.appendChild(tdName);

                // Type
                const tdType = document.createElement('td');
                const badge = document.createElement('span');
                badge.className = `badge-type badge-${lead.type.toLowerCase()}`;
                badge.textContent = lead.type;
                tdType.appendChild(badge);
                tr.appendChild(tdType);

                // City
                const tdCity = document.createElement('td');
                tdCity.textContent = lead.city;
                tr.appendChild(tdCity);

                // Phone
                const tdPhone = document.createElement('td');
                tdPhone.textContent = lead.phone;
                tr.appendChild(tdPhone);

                // Action
                const tdAction = document.createElement('td');
                tdAction.className = "text-end";
                const btn = document.createElement('button');
                btn.className = "btn btn-whatsapp btn-sm";
                btn.innerHTML = '<i class="fab fa-whatsapp me-1"></i> Send WhatsApp';
                btn.onclick = function() {
                    sendWhatsApp(lead.id, lead.phone, lead.name, lead.type);
                };
                tdAction.appendChild(btn);
                tr.appendChild(tdAction);

                tbody.appendChild(tr);
            });
        });
}

function triggerCollection() {
    fetch('/api/trigger_collection', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Wait a moment for collection to happen
                setTimeout(fetchLeads, 500);
            }
        });
}

function getNextWeekday() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const d = new Date();
    d.setDate(d.getDate() + 1); // Tomorrow
    // If it's Sunday (0), make it Monday
    if (d.getDay() === 0) {
        d.setDate(d.getDate() + 1);
    }
    // If it's Saturday (6), make it Monday
    if (d.getDay() === 6) {
        d.setDate(d.getDate() + 2);
    }
    return days[d.getDay()];
}

function sendWhatsApp(id, phone, name, type) {
    // 1. Generate Message
    const dayOfWeek = getNextWeekday();
    let sector = "Services";
    let entity = "Service Provider";
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";

    if (type === 'Clinic') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (type === 'Store') {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse products";
        focus = "sales";
    }

    // Using template literal for multiline string.
    // Note: WhatsApp URL encoding handles newlines as %0A
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    const encodedMessage = encodeURIComponent(message);
    const whatsappUrl = `https://wa.me/${phone.replace(/\s+/g, '')}?text=${encodedMessage}`;

    // 2. Open WhatsApp in new tab
    window.open(whatsappUrl, '_blank');

    // 3. Mark as contacted in backend
    // We do this concurrently so the UI updates immediately or after API returns
    fetch(`/api/leads/${id}/contact`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 4. Refresh list
                fetchLeads();
            }
        });
}
