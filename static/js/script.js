document.addEventListener('DOMContentLoaded', () => {
    loadAnalytics();
    loadLeads();
    document.getElementById('leads-table').addEventListener('click', handleWhatsAppClick);
});

async function handleWhatsAppClick(e) {
    if(!e.target.classList.contains('btn-whatsapp')) return;

    const btn = e.target;
    const id = btn.dataset.id;
    const name = btn.dataset.name;
    const type = btn.dataset.type;
    let phone = btn.dataset.phone;

    // Format Pakistani phone number to standard international format without '+' for wa.me
    // e.g. 0300-1234567 -> 923001234567
    phone = phone.replace(/[-\s]/g, '').replace(/^0/, '92');

    const message = encodeURIComponent(generateWhatsAppPitch(name, type));
    const waUrl = `https://wa.me/${phone}?text=${message}`;

    // Open synchronously to avoid popup blockers
    window.open(waUrl, '_blank');

    // Optimistic UI update
    const row = btn.closest('tr');
    if (row) {
        row.remove();
    }

    // Call API
    try {
        await fetch('/api/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        // Reload analytics
        loadAnalytics();
    } catch (e) {
        console.error("Failed to mark as contacted:", e);
    }
}

function generateWhatsAppPitch(businessName, businessType) {
    let clients = "Clients";
    let action = "book appointments";
    let focus = "services";
    let entity = businessType;
    let sector = businessType;

    if (businessType.toLowerCase().includes('clinic')) {
        clients = "Patients";
        action = "book appointments";
        focus = "care";
        sector = "Healthcare";
    } else if (businessType.toLowerCase().includes('retail') || businessType.toLowerCase().includes('store')) {
        clients = "Customers";
        action = "buy products";
        focus = "sales";
        sector = "Retail";
    } else if (businessType.toLowerCase().includes('service')) {
        clients = "Clients";
        action = "book appointments";
        focus = "services";
        sector = "Services";
    }

    const today = new Date();
    const chatDate = new Date(today);
    chatDate.setDate(chatDate.getDate() + 2);
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

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        if(data && !data.error) {
            document.getElementById('total-leads').textContent = data.total;
            document.getElementById('contacted-leads').textContent = data.contacted;
        }
    } catch (e) {
        console.error("Error loading analytics:", e);
    }
}

async function loadLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();

        const tbody = document.getElementById('leads-body');
        tbody.innerHTML = '';

        if(leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No active leads found. Scraping may be in progress.</td></tr>';
            return;
        }

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.dataset.id = lead.id;

            tr.innerHTML = `
                <td>${escapeHTML(lead.business_name)}</td>
                <td>${escapeHTML(lead.type)}</td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp" data-id="${lead.id}" data-name="${escapeHTML(lead.business_name)}" data-type="${escapeHTML(lead.type)}" data-phone="${escapeHTML(lead.phone)}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (e) {
        console.error("Error loading leads:", e);
    }
}
