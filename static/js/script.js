document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData();

    // Set up polling every 30 seconds
    setInterval(fetchData, 30000);

    // Event delegation for table buttons
    document.getElementById('leads-body').addEventListener('click', handleTableClick);
});

async function handleTableClick(e) {
    const button = e.target.closest('button[data-action="whatsapp"]');
    if (!button) return;

    e.preventDefault();

    const id = button.dataset.id;
    const name = button.dataset.name;
    const type = button.dataset.type;
    const phone = button.dataset.phone;

    // Generate dynamic message
    const message = generateWhatsAppMessage(name, type);

    // Format phone number to remove spaces/symbols for wa.me API
    const formattedPhone = phone.replace(/[^0-9]/g, '');

    // Create WhatsApp URL
    const waUrl = `https://wa.me/${formattedPhone}?text=${encodeURIComponent(message)}`;

    // Open WhatsApp URL synchronously to avoid popup blockers
    window.open(waUrl, '_blank');

    // Update UI state
    button.classList.add('loading');
    button.disabled = true;

    try {
        // Mark as contacted in the backend
        const response = await fetch(`/api/leads/${id}/contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Remove the row from the table smoothly
            const row = button.closest('tr');
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                // Fetch new data to update stats and table
                fetchData();
            }, 300);
        } else {
            console.error('Failed to mark lead as contacted.');
            button.classList.remove('loading');
            button.disabled = false;
        }
    } catch (error) {
        console.error('Error updating lead status:', error);
        button.classList.remove('loading');
        button.disabled = false;
    }
}

function generateWhatsAppMessage(businessName, type) {
    // Defaults for general
    let sector = "Local";
    let entity = "Business";
    let clients = "Customers";
    let action = "discover what you offer";
    let focus = "daily operations";

    // Dynamic adaptation based on type
    if (type.toLowerCase().includes('clinic') || type.toLowerCase().includes('health')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "providing care";
    } else if (type.toLowerCase().includes('store') || type.toLowerCase().includes('retail') || type.toLowerCase().includes('shop')) {
        sector = "Retail";
        entity = "Store";
        clients = "Customers";
        action = "browse and buy products";
        focus = "generating sales";
    } else if (type.toLowerCase().includes('service')) {
        sector = "Services";
        entity = "Service Provider";
        clients = "Clients";
        action = "book your services";
        focus = "delivering quality services";
    }

    const today = new Date();
    // Suggest meeting in 2 days
    today.setDate(today.getDate() + 2);
    const options = { weekday: 'long' };
    const meetingDay = today.toLocaleDateString('en-US', options);

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

I would love to discuss how we can help your ${entity} thrive online. Are you available for a brief chat on ${meetingDay}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
}

async function fetchData() {
    try {
        const [statsResponse, leadsResponse] = await Promise.all([
            fetch('/api/stats'),
            fetch('/api/leads')
        ]);

        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            updateStats(stats);
        }

        if (leadsResponse.ok) {
            const leads = await leadsResponse.json();
            updateLeadsTable(leads);
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateStats(stats) {
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-new').textContent = stats.new;
    document.getElementById('stat-contacted').textContent = stats.contacted;
}

function updateLeadsTable(leads) {
    const tbody = document.getElementById('leads-body');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    const table = document.getElementById('leads-table');

    loadingState.style.display = 'none';

    if (leads.length === 0) {
        table.style.display = 'none';
        emptyState.style.display = 'block';
        tbody.innerHTML = '';
        return;
    }

    table.style.display = 'table';
    emptyState.style.display = 'none';

    tbody.innerHTML = '';

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.dataset.leadId = lead.id;

        tr.innerHTML = `
            <td><strong>${escapeHtml(lead.business_name)}</strong></td>
            <td><span class="type-badge">${escapeHtml(lead.type)}</span></td>
            <td>${escapeHtml(lead.city)}</td>
            <td>${escapeHtml(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp" data-action="whatsapp" data-id="${lead.id}"
                        data-name="${escapeHtml(lead.business_name)}" data-type="${escapeHtml(lead.type)}"
                        data-phone="${escapeHtml(lead.phone)}">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                    </svg>
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
         .toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
