document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData();

    // Poll APIs every 30 seconds
    setInterval(fetchData, 30000);

    // Event delegation for WhatsApp buttons
    document.getElementById('leads-body').addEventListener('click', async (e) => {
        const btn = e.target.closest('.send-whatsapp');
        if (!btn) return;

        const tr = btn.closest('tr');
        const id = tr.dataset.id;
        const phone = tr.dataset.phone;
        const name = tr.dataset.name;
        const type = tr.dataset.type;

        handleWhatsAppClick(id, phone, name, type, tr);
    });
});

function handleWhatsAppClick(id, phone, name, type, rowElement) {
    // 1. Generate Message
    const message = generateWhatsAppMessage(name, type);

    // 2. Format phone number for wa.me (remove spaces, +, etc)
    const cleanPhone = phone.replace(/\D/g, '');

    // 3. Open WhatsApp synchronously to prevent popup blockers
    const waUrl = `https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');

    // 4. Optimistic UI update
    rowElement.style.opacity = '0.5';
    rowElement.style.pointerEvents = 'none';

    // 5. Update backend asynchronously
    markAsContacted(id, rowElement);
}

function generateWhatsAppMessage(businessName, businessType) {
    const typeStr = businessType.toLowerCase();

    // Variables that adapt based on type
    let sector = "Retail";
    let entity = "Store";
    let clients = "Customers";
    let action = "browse products";
    let focus = "sales";

    if (typeStr.includes('clinic') || typeStr.includes('health') || typeStr.includes('care')) {
        sector = "Healthcare";
        entity = "Clinic";
        clients = "Patients";
        action = "book appointments";
        focus = "care";
    } else if (typeStr.includes('service') || typeStr.includes('repair') || typeStr.includes('plumb')) {
        sector = "Services";
        entity = "Service";
        clients = "Clients";
        action = "book appointments";
        focus = "services";
    }

    // Propose chat day (2 days from now)
    const chatDate = new Date();
    chatDate.setDate(chatDate.getDate() + 2);
    const dayOptions = { weekday: 'long' };
    const chatDay = new Intl.DateTimeFormat('en-US', dayOptions).format(chatDate);

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

async function markAsContacted(id, rowElement) {
    try {
        const response = await fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: id })
        });

        if (response.ok) {
            // Remove row from UI completely
            rowElement.remove();
            // Refresh stats to reflect the change
            fetchStats();

            // If table is now empty, fetch leads again to see if new ones arrived
            if (document.getElementById('leads-body').children.length === 0) {
                fetchLeads();
            }
        } else {
            // Revert optimistic update on failure
            console.error("Failed to update status");
            rowElement.style.opacity = '1';
            rowElement.style.pointerEvents = 'auto';
            alert("Failed to mark as contacted. Please try again.");
        }
    } catch (error) {
        console.error("Error updating contact status:", error);
        rowElement.style.opacity = '1';
        rowElement.style.pointerEvents = 'auto';
    }
}

async function fetchData() {
    try {
        await Promise.all([
            fetchStats(),
            fetchLeads()
        ]);
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

async function fetchStats() {
    const response = await fetch('/api/stats');
    if (!response.ok) throw new Error('Failed to fetch stats');
    const data = await response.json();

    document.getElementById('total-leads').textContent = data.total;
    document.getElementById('new-leads').textContent = data.new;
    document.getElementById('contacted-leads').textContent = data.contacted;
}

async function fetchLeads() {
    const response = await fetch('/api/leads');
    if (!response.ok) throw new Error('Failed to fetch leads');
    const leads = await response.json();

    renderLeads(leads);
}

function renderLeads(leads) {
    const tbody = document.getElementById('leads-body');
    tbody.innerHTML = '';

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No new leads available. Checking for new opportunities...</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.dataset.id = lead.id;
        tr.dataset.phone = lead.phone;
        tr.dataset.name = lead.business_name;
        tr.dataset.type = lead.type;

        // Define badge color based on type
        let badgeColor = '#6c757d'; // Default grey
        let typeStr = lead.type.toLowerCase();
        if (typeStr.includes('clinic')) badgeColor = '#007bff'; // Blue
        else if (typeStr.includes('store')) badgeColor = '#28a745'; // Green
        else if (typeStr.includes('service')) badgeColor = '#17a2b8'; // Cyan

        // Escape HTML to prevent XSS
        const escapeHtml = (unsafe) => {
            return (unsafe || '').toString()
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        };

        tr.innerHTML = `
            <td><strong>${escapeHtml(lead.business_name)}</strong></td>
            <td><span class="type-badge" style="background-color: ${badgeColor}20; color: ${badgeColor}; border: 1px solid ${badgeColor}40;">${escapeHtml(lead.type)}</span></td>
            <td>${escapeHtml(lead.city)}</td>
            <td>${escapeHtml(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp send-whatsapp" data-id="${lead.id}">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592zm3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.729.729 0 0 0-.529.247c-.182.198-.691.677-.691 1.654 0 .977.71 1.916.81 2.049.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z"/>
                    </svg>
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}
