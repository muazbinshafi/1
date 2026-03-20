document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();

    // Poll every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, 30000);

    // Event delegation for dynamically added WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', (event) => {
        const btn = event.target.closest('.btn-whatsapp');
        if (btn) {
            const row = btn.closest('tr');
            const leadId = btn.getAttribute('data-id');
            const businessName = btn.getAttribute('data-name');
            const businessType = btn.getAttribute('data-type');
            const phone = btn.getAttribute('data-phone');

            // 1. Send WhatsApp Message (Synchronous before API call to avoid popup blockers)
            const message = generateWhatsAppMessage(businessName, businessType);
            const formattedPhone = phone.replace(/[^0-9]/g, ''); // Remove non-numeric chars
            const waUrl = `https://wa.me/${formattedPhone}?text=${encodeURIComponent(message)}`;

            window.open(waUrl, '_blank');

            // 2. Optimistic UI update: Remove row immediately
            row.remove();

            // 3. Backend status update (mark contacted)
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: leadId }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`Lead ${leadId} marked as contacted.`);
                    fetchStats(); // Update analytics
                } else {
                    console.error('Failed to mark lead as contacted.');
                }
            })
            .catch(error => {
                console.error('Error marking lead as contacted:', error);
            });
        }
    });
});

function fetchStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            if(data.error) return;
            document.getElementById('total-leads').textContent = data.total || 0;
            document.getElementById('new-leads').textContent = data.new || 0;
            document.getElementById('contacted-leads').textContent = data.contacted || 0;
        })
        .catch(err => console.error("Error fetching stats:", err));
}

function fetchLeads() {
    fetch('/api/leads')
        .then(res => res.json())
        .then(leads => {
            if(leads.error) return;
            const tbody = document.getElementById('leads-body');
            tbody.innerHTML = ''; // Clear existing rows

            if (leads.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No new leads available.</td></tr>';
                return;
            }

            leads.forEach(lead => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${lead.business_name}</td>
                    <td>${lead.type}</td>
                    <td>${lead.city}</td>
                    <td>${lead.phone}</td>
                    <td>
                        <button
                            class="btn-whatsapp"
                            data-id="${lead.id}"
                            data-name="${lead.business_name}"
                            data-type="${lead.type}"
                            data-phone="${lead.phone}">
                            Send WhatsApp
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error("Error fetching leads:", err));
}

function generateWhatsAppMessage(businessName, type) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = new Date();
    const chatDate = new Date(today);
    chatDate.setDate(chatDate.getDate() + 2); // 2 days from now
    const chatDay = days[chatDate.getDay()];

    let sector = type;
    let entity = type;
    let clients = 'Customers';
    let action = 'buy products';
    let focus = 'sales';

    // Dynamic adaptation
    if (type.toLowerCase() === 'clinic') {
        sector = 'Healthcare';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (type.toLowerCase() === 'store') {
        sector = 'Retail';
        clients = 'Customers';
        action = 'browse products';
        focus = 'sales';
    } else if (type.toLowerCase() === 'service') {
        sector = 'Services';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

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
