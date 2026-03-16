document.addEventListener('DOMContentLoaded', () => {
    fetchLeads();
    fetchStats();

    // Poll APIs every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);

    // Event Delegation for "Send WhatsApp" actions
    document.getElementById('leads-body').addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const button = e.target;
            const leadId = button.dataset.id;
            const businessName = button.dataset.name;
            const businessType = button.dataset.type;
            const phone = button.dataset.phone;

            sendWhatsApp(leadId, businessName, businessType, phone, button);
        }
    });
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('total-leads').innerText = data.total;
        document.getElementById('contacted-leads').innerText = data.contacted;
        document.getElementById('new-leads').innerText = data.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        const tbody = document.getElementById('leads-body');
        const loadingMsg = document.getElementById('loading-msg');
        const noLeadsMsg = document.getElementById('no-leads-msg');

        loadingMsg.style.display = 'none';

        if (leads.length === 0) {
            noLeadsMsg.style.display = 'block';
            tbody.innerHTML = '';
            return;
        } else {
            noLeadsMsg.style.display = 'none';
        }

        // Build table rows
        let rows = '';
        leads.forEach(lead => {
            rows += `
                <tr id="row-${lead.id}">
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
                </tr>
            `;
        });

        tbody.innerHTML = rows;
    } catch (error) {
        console.error('Error fetching leads:', error);
        document.getElementById('loading-msg').innerText = 'Failed to load leads.';
    }
}

function sendWhatsApp(id, name, type, phone, buttonElement) {
    const messageTemplate = generateMessage(name, type);

    // Format phone number to clean E.164-like structure if it's local
    // e.g., 03001234567 -> 923001234567
    let cleanPhone = phone.replace(/[^0-9+]/g, '');
    if (cleanPhone.startsWith('0')) {
        cleanPhone = '92' + cleanPhone.substring(1);
    }

    const waUrl = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(messageTemplate)}`;

    // Open WA synchronous before calling backend to bypass popup blockers
    window.open(waUrl, '_blank');

    // Mark as contacted in backend
    markContacted(id, buttonElement);
}

function generateMessage(businessName, businessType) {
    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    const typeLower = businessType.toLowerCase();

    if (typeLower.includes("clinic") || typeLower.includes("health") || typeLower.includes("hospital")) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower.includes("service") || typeLower.includes("repair") || typeLower.includes("plumb")) {
        sector = "Services";
        entity = "Service Provider";
        clients = "Clients";
        action = "book services";
        focus = "services";
    }

    // Dynamic proposal day logic
    const today = new Date();
    today.setDate(today.getDate() + 2); // Propose chat 2 days from now
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const proposedDay = days[today.getDay()];

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${proposedDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

async function markContacted(id, buttonElement) {
    buttonElement.innerText = "Processing...";
    buttonElement.disabled = true;

    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ lead_id: id })
        });

        if (response.ok) {
            // Hide row and update stats without full reload
            const row = document.getElementById(`row-${id}`);
            if (row) {
                row.style.opacity = '0.5';
                setTimeout(() => {
                    row.remove();
                    // Check if empty
                    if (document.getElementById('leads-body').children.length === 0) {
                        document.getElementById('no-leads-msg').style.display = 'block';
                    }
                }, 500);
            }
            fetchStats();
        } else {
            console.error('Failed to mark as contacted');
            buttonElement.innerText = "Error";
            buttonElement.disabled = false;
        }
    } catch (error) {
        console.error('Error in markContacted:', error);
        buttonElement.innerText = "Error";
        buttonElement.disabled = false;
    }
}
