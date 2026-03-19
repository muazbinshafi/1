document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchLeads();
    fetchStats();

    // Poll every 30 seconds
    setInterval(() => {
        fetchLeads();
        fetchStats();
    }, 30000);
});

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('stat-total').textContent = data.total;
        document.getElementById('stat-contacted').textContent = data.contacted;
        document.getElementById('stat-new').textContent = data.new;
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeads() {
    try {
        const response = await fetch('/api/leads');
        const leads = await response.json();
        const tbody = document.getElementById('leads-body');

        tbody.innerHTML = ''; // Clear existing rows

        if (leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666;">No uncontacted leads currently available. Background scraping may be in progress.</td></tr>';
            return;
        }

        leads.forEach(lead => {
            const tr = document.createElement('tr');

            // Determine badge class
            let badgeClass = 'badge-service';
            if (lead.type.toLowerCase() === 'clinic') badgeClass = 'badge-clinic';
            else if (lead.type.toLowerCase() === 'store') badgeClass = 'badge-store';

            // We use encodeURIComponent to safely pass data in data attributes
            const safeName = lead.business_name.replace(/"/g, '&quot;');

            tr.innerHTML = `
                <td><strong>${lead.business_name}</strong></td>
                <td><span class="badge ${badgeClass}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp"
                            data-id="${lead.id}"
                            data-name="${safeName}"
                            data-type="${lead.type}"
                            data-phone="${lead.phone}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.247c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232"/>
                        </svg>
                        Send WhatsApp
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching leads:', error);
    }
}

// Event Delegation for dynamically generated buttons
document.getElementById('leads-table').addEventListener('click', async (e) => {
    // Find nearest button in case click was on SVG
    const btn = e.target.closest('.btn-whatsapp');
    if (!btn) return;

    // 1. Get data
    const leadId = btn.getAttribute('data-id');
    const bName = btn.getAttribute('data-name');
    const rawType = btn.getAttribute('data-type');
    const phone = btn.getAttribute('data-phone');

    // 2. Generate dynamic message template
    const typeStr = rawType.toLowerCase();
    let entity, clients, action, focus, sector;

    if (typeStr === 'clinic') {
        sector = 'Healthcare';
        entity = 'Clinic';
        clients = 'Patients';
        action = 'book appointments';
        focus = 'care';
    } else if (typeStr === 'store') {
        sector = 'Retail';
        entity = 'Store';
        clients = 'Customers';
        action = 'browse products';
        focus = 'sales';
    } else {
        sector = 'Services';
        entity = 'Service Business';
        clients = 'Clients';
        action = 'book appointments';
        focus = 'services';
    }

    // Propose a chat day dynamically: 2 days from now
    const d = new Date();
    d.setDate(d.getDate() + 2);
    const dayName = d.toLocaleDateString('en-US', { weekday: 'long' });

    const message = `Hello ${bName} 👋,
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
I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${dayName}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

    // 3. Open WhatsApp synchronously to prevent popup blocker
    // Ensure phone number format is wa.me compatible (digits only)
    const cleanPhone = phone.replace(/[^0-9]/g, '');
    const waUrl = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');

    // Remove row from UI optimistically
    btn.closest('tr').remove();

    // 4. Send POST request to mark as contacted
    try {
        const res = await fetch('/api/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: leadId })
        });

        if (res.ok) {
            // Update stats immediately
            const total = parseInt(document.getElementById('stat-total').textContent);
            let contacted = parseInt(document.getElementById('stat-contacted').textContent);

            contacted++;
            document.getElementById('stat-contacted').textContent = contacted;
            document.getElementById('stat-new').textContent = total - contacted;
        }
    } catch (error) {
        console.error('Failed to mark lead as contacted:', error);
    }
});
