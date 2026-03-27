document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData();

    // Poll every 30 seconds
    setInterval(fetchData, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-whatsapp');
        if (!btn) return;

        const row = btn.closest('tr');
        const leadId = row.dataset.id;
        const businessName = row.dataset.name;
        const type = row.dataset.type;
        const phone = row.dataset.phone;

        // Generate customized message
        const message = generatePitch(businessName, type);
        const encodedMessage = encodeURIComponent(message);

        // Format phone number (remove spaces, ensure country code)
        let formattedPhone = phone.replace(/\s+/g, '');
        if (formattedPhone.startsWith('0')) {
            formattedPhone = '+92' + formattedPhone.substring(1);
        } else if (!formattedPhone.startsWith('+')) {
            formattedPhone = '+' + formattedPhone;
        }

        const whatsappUrl = `https://wa.me/${formattedPhone}?text=${encodedMessage}`;

        // 1. Open WhatsApp synchronously to avoid popup blockers
        window.open(whatsappUrl, '_blank');

        // 2. Optimistic UI update
        row.style.opacity = '0.5';
        row.style.pointerEvents = 'none';

        // 3. Backend update
        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: leadId })
            });

            if (response.ok) {
                // Remove row with animation
                row.style.transition = 'opacity 0.3s ease';
                row.style.opacity = '0';
                setTimeout(() => {
                    row.remove();
                    // Update stats locally
                    updateStatsLocally();
                    checkEmptyTable();
                }, 300);
            } else {
                // Revert optimistic update on failure
                row.style.opacity = '1';
                row.style.pointerEvents = 'auto';
                console.error('Failed to update lead status');
            }
        } catch (error) {
            row.style.opacity = '1';
            row.style.pointerEvents = 'auto';
            console.error('Error updating lead status:', error);
        }
    });
});

async function fetchData() {
    try {
        const [leadsRes, statsRes] = await Promise.all([
            fetch('/api/leads'),
            fetch('/api/stats')
        ]);

        const leads = await leadsRes.json();
        const stats = await statsRes.json();

        renderLeads(leads);
        renderStats(stats);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function renderStats(stats) {
    document.getElementById('stat-new').textContent = stats.new;
    document.getElementById('stat-contacted').textContent = stats.contacted;
    document.getElementById('stat-total').textContent = stats.total;
}

function updateStatsLocally() {
    const newEl = document.getElementById('stat-new');
    const contactedEl = document.getElementById('stat-contacted');

    let newCount = parseInt(newEl.textContent);
    let contactedCount = parseInt(contactedEl.textContent);

    if (newCount > 0) {
        newEl.textContent = newCount - 1;
        contactedEl.textContent = contactedCount + 1;
    }
}

function escapeHTML(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function renderLeads(leads) {
    const tbody = document.getElementById('leads-body');

    if (leads.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">No active leads found. New leads are being collected.</td></tr>`;
        return;
    }

    const rowsHTML = leads.map(lead => `
        <tr data-id="${lead.id}" data-name="${escapeHTML(lead.business_name)}" data-type="${escapeHTML(lead.type)}" data-phone="${escapeHTML(lead.phone)}">
            <td><strong>${escapeHTML(lead.business_name)}</strong></td>
            <td><span class="badge ${escapeHTML(lead.type).toLowerCase()}">${escapeHTML(lead.type)}</span></td>
            <td>${escapeHTML(lead.city)}</td>
            <td>${escapeHTML(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    Send WhatsApp
                </button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rowsHTML;
}

function checkEmptyTable() {
    const tbody = document.getElementById('leads-body');
    if (tbody.children.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">All caught up! Waiting for new leads...</td></tr>`;
    }
}

function getNextChatDay() {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const today = new Date();
    // Propose a day 2 days from now
    const targetDay = new Date(today);
    targetDay.setDate(today.getDate() + 2);
    return days[targetDay.getDay()];
}

function generatePitch(businessName, businessType) {
    const typeLower = businessType.toLowerCase();

    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "buy products";
    let focus = "sales";

    if (typeLower.includes('clinic')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeLower.includes('service')) {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    const chatDay = getNextChatDay();

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
