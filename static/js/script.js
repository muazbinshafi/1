document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    updateStats();

    // Poll every 30 seconds
    setInterval(() => {
        fetchLeads();
        updateStats();
    }, 30000);

    document.getElementById('refresh-btn').addEventListener('click', () => {
        fetchLeads();
        updateStats();
    });

    document.getElementById('collect-btn').addEventListener('click', manualCollect);
});

function fetchLeads() {
    fetch('/api/leads')
        .then(response => response.json())
        .then(leads => {
            const tableBody = document.querySelector('#leads-table tbody');
            tableBody.innerHTML = ''; // Clear existing

            if (leads.length === 0) {
                const row = document.createElement('tr');
                row.innerHTML = '<td colspan="5" style="text-align:center;">No new leads available. Waiting for collection...</td>';
                tableBody.appendChild(row);
                return;
            }

            leads.forEach(lead => {
                const row = document.createElement('tr');

                // Create cells
                const nameCell = document.createElement('td');
                nameCell.textContent = lead.business_name;

                const typeCell = document.createElement('td');
                const badge = document.createElement('span');
                badge.className = `badge ${lead.type.toLowerCase()}`;
                badge.textContent = lead.type;
                typeCell.appendChild(badge);

                const cityCell = document.createElement('td');
                cityCell.textContent = lead.city;

                const phoneCell = document.createElement('td');
                phoneCell.textContent = lead.phone;

                const actionCell = document.createElement('td');
                const btn = document.createElement('button');
                btn.className = 'btn-whatsapp';
                btn.innerHTML = '<i class="fab fa-whatsapp"></i> Send WhatsApp';
                btn.onclick = () => sendWhatsApp(btn, lead.id, lead.business_name, lead.type, lead.phone);
                actionCell.appendChild(btn);

                row.appendChild(nameCell);
                row.appendChild(typeCell);
                row.appendChild(cityCell);
                row.appendChild(phoneCell);
                row.appendChild(actionCell);

                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching leads:', error));
}

function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            document.getElementById('total-leads').textContent = stats.total;
            document.getElementById('contacted-leads').textContent = stats.contacted;
            document.getElementById('new-leads').textContent = stats.new;
        })
        .catch(error => console.error('Error fetching stats:', error));
}

function manualCollect() {
    const btn = document.getElementById('collect-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Collecting...';
    btn.disabled = true;

    fetch('/api/collect', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Wait a bit to let the collection happen (if async) or just refresh
            setTimeout(() => {
                fetchLeads();
                updateStats();
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 2000);
        })
        .catch(error => {
            console.error('Error collecting:', error);
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function sendWhatsApp(btnElement, id, businessName, type, phone) {
    // Generate message
    const message = generateMessage(businessName, type);

    // Encode for URL
    const encodedMessage = encodeURIComponent(message);

    // Clean phone number (remove spaces, ensure international format)
    // Assuming mock data has valid +92 format with spaces.
    const cleanPhone = phone.replace(/\s+/g, '').replace(/^\+/, '');

    // Construct URL
    const url = `https://wa.me/${cleanPhone}?text=${encodedMessage}`;

    // Open in new tab
    window.open(url, '_blank');

    // Mark as contacted in backend
    markAsContacted(id, btnElement);
}

function markAsContacted(id, btnElement) {
    fetch(`/api/contact/${id}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI: Remove row or mark as sent
                // Animation to remove row
                const row = btnElement.closest('tr');
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                    updateStats();
                    // If table is empty, fetch again or show message
                    if (document.querySelector('#leads-table tbody').children.length === 0) {
                        fetchLeads();
                    }
                }, 500);
            }
        })
        .catch(error => console.error('Error marking contacted:', error));
}

function generateMessage(businessName, type) {
    // Dynamic Terminology
    let sector = "Business";
    let entity = "Business";
    let clients = "Clients";
    let action = "avail services";
    let focus = "operations";

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
        action = "buy products";
        focus = "sales";
    } else if (type === 'Service') {
        sector = "Service";
        entity = "Service";
        clients = "Clients";
        action = "book appointments"; // or avail services
        focus = "services";
    }

    // Get current day of week
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayOfWeek = days[new Date().getDay()];

    // Template
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}
