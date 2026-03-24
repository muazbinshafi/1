document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    fetchDashboardData();

    // Poll for updates every 30 seconds
    setInterval(fetchDashboardData, 30000);

    // Event delegation for WhatsApp buttons
    const leadsBody = document.getElementById('leads-body');
    leadsBody.addEventListener('click', (e) => {
        // Find closest button if clicking inside the button
        const btn = e.target.closest('.btn-whatsapp');
        if (!btn) return;

        const leadId = btn.dataset.id;
        const businessName = btn.dataset.name;
        const type = btn.dataset.type;
        const phone = btn.dataset.phone;

        handleWhatsAppOutreach(leadId, businessName, type, phone, btn.closest('tr'));
    });
});

async function fetchDashboardData() {
    try {
        const [statsResponse, leadsResponse] = await Promise.all([
            fetch('/api/stats'),
            fetch('/api/leads')
        ]);

        if (statsResponse.ok && leadsResponse.ok) {
            const stats = await statsResponse.json();
            const leads = await leadsResponse.json();

            updateStatsUI(stats);
            updateLeadsUI(leads);
        } else {
            console.error('Failed to fetch dashboard data.');
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

function updateStatsUI(stats) {
    document.getElementById('total-leads-count').textContent = stats.total_leads;
    document.getElementById('contacted-leads-count').textContent = stats.contacted_leads;
    document.getElementById('new-leads-count').textContent = stats.new_leads;

    // Calculate outreach progress (Contacted / Total)
    const outreachProgress = document.getElementById('outreach-progress');
    let percentage = 0;
    if (stats.total_leads > 0) {
        percentage = Math.round((stats.contacted_leads / stats.total_leads) * 100);
    }
    outreachProgress.style.width = `${percentage}%`;
}

function updateLeadsUI(leads) {
    const tbody = document.getElementById('leads-body');
    tbody.innerHTML = '';

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading-cell">No uncontacted leads available. Background collection may be running.</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHTML(lead.business_name)}</strong></td>
            <td><span style="background:#e0f7fa; padding:2px 8px; border-radius:12px; font-size:12px; color:#006064">${escapeHTML(lead.type)}</span></td>
            <td>${escapeHTML(lead.city)}</td>
            <td>${escapeHTML(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp"
                    data-id="${lead.id}"
                    data-name="${escapeHTML(lead.business_name)}"
                    data-type="${escapeHTML(lead.type)}"
                    data-phone="${escapeHTML(lead.phone)}">
                    💬 Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function handleWhatsAppOutreach(id, businessName, type, phone, rowElement) {
    // 1. Generate customized message
    const message = generatePitch(businessName, type);

    // 2. Format phone number (remove non-digits, ensure country code)
    // If it starts with 0 (like 03001234567), replace 0 with +92
    let formattedPhone = phone.replace(/[^\d+]/g, '');
    if (formattedPhone.startsWith('0')) {
        formattedPhone = '+92' + formattedPhone.substring(1);
    }

    // 3. Create wa.me URL
    const encodedMessage = encodeURIComponent(message);
    const whatsappUrl = `https://wa.me/${formattedPhone.replace('+', '')}?text=${encodedMessage}`;

    // 4. Open WhatsApp synchronously in a new tab (prevents popup blockers)
    window.open(whatsappUrl, '_blank', 'noopener,noreferrer');

    // 5. Optimistically update UI (hide row)
    rowElement.style.display = 'none';

    // 6. Notify Backend asynchronously
    markLeadContacted(id).then(success => {
        if (!success) {
            // Revert UI if it failed
            rowElement.style.display = '';
            console.error('Failed to mark lead as contacted in database.');
        } else {
             // Refresh stats to show update
             fetchDashboardData();
        }
    });
}

async function markLeadContacted(id) {
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: parseInt(id) })
        });
        return response.ok;
    } catch (error) {
        console.error('Error marking lead contacted:', error);
        return false;
    }
}

function generatePitch(businessName, type) {
    // Determine dynamic terms based on business type
    let sector = type || "Business";
    let entity = type || "Business";
    let clients = "Clients";
    let action = "utilize your services";
    let focus = "your operations";

    const typeLower = type ? type.toLowerCase() : "";
    if (typeLower.includes("clinic") || typeLower.includes("hospital")) {
        clients = "Patients";
        action = "book appointments";
        focus = "providing excellent care";
        entity = "Clinic";
        sector = "Healthcare";
    } else if (typeLower.includes("store") || typeLower.includes("retail") || typeLower.includes("shop")) {
        clients = "Customers";
        action = "browse and buy products";
        focus = "boosting sales";
        entity = "Store";
        sector = "Retail";
    } else {
        // Services default
        clients = "Clients";
        action = "book your services";
        focus = "delivering quality service";
        entity = "Service Provider";
        sector = "Local Services";
    }

    // Determine target day (e.g., +2 days from now)
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + 2);
    const options = { weekday: 'long' };
    const targetDay = new Intl.DateTimeFormat('en-US', options).format(targetDate);

    // Construct the pitch according to the prompt template
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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${targetDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

// Utility to prevent XSS
function escapeHTML(str) {
    if (!str) return '';
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