document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();
    setInterval(fetchStats, 30000);
    setInterval(fetchLeads, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', handleWhatsAppClick);
});

function getWhatsAppMessage(businessName, businessType) {
    const typeLower = businessType.toLowerCase();

    let sector = "Business";
    let entity = "Business";
    let clients = "Clients";
    let action = "use your services";
    let focus = "your business operations";

    if (typeLower === 'clinic') {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower === 'store' || typeLower === 'retail') {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "buy products";
        focus = "sales";
    } else if (typeLower === 'service') {
        sector = "Services";
        entity = "Service Provider";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const today = new Date();
    const chatDate = new Date(today);
    chatDate.setDate(today.getDate() + 2);
    const dayOfWeek = chatDate.toLocaleDateString('en-US', { weekday: 'long' });

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

async function handleWhatsAppClick(e) {
    if (e.target.classList.contains('whatsapp-btn')) {
        const btn = e.target;
        const id = btn.dataset.id;
        const name = btn.dataset.name;
        const type = btn.dataset.type;
        const phone = btn.dataset.phone;

        // Clean phone number: remove spaces and non-digits (except leading +)
        const cleanedPhone = phone.replace(/[^\d+]/g, '');
        const message = encodeURIComponent(getWhatsAppMessage(name, type));
        const whatsappUrl = `https://wa.me/${cleanedPhone}?text=${message}`;

        // Open WhatsApp in a new tab synchronously to avoid popup blockers
        window.open(whatsappUrl, '_blank');

        // Call backend to mark as contacted
        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id: id })
            });

            if (response.ok) {
                // Remove the row from the table
                const tr = btn.closest('tr');
                if (tr) {
                    tr.remove();
                }
                // Refresh stats
                fetchStats();

                // Automatically collect new leads
                try {
                    await fetch('/api/collect', { method: 'POST' });
                } catch (e) {
                    console.error('Error triggering collection:', e);
                }
            } else {
                console.error('Failed to mark lead as contacted');
            }
        } catch (error) {
            console.error('Error updating lead status:', error);
        }
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        document.getElementById('total-leads').innerText = data.total;
        document.getElementById('new-leads').innerText = data.new;
        document.getElementById('contacted-leads').innerText = data.contacted;
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
            tr.dataset.id = lead.id;
            tr.innerHTML = `
                <td>${lead.business_name}</td>
                <td>${lead.type}</td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td><button class="whatsapp-btn" data-id="${lead.id}" data-name="${lead.business_name}" data-type="${lead.type}" data-phone="${lead.phone}">Send WhatsApp</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}
