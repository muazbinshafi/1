document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData();

    // Poll every 30 seconds
    setInterval(fetchData, 30000);

    // Event delegation for WhatsApp buttons
    const leadsBody = document.getElementById('leads-body');
    leadsBody.addEventListener('click', handleWhatsAppClick);
});

async function fetchData() {
    try {
        const [leadsRes, statsRes] = await Promise.all([
            fetch('/api/leads'),
            fetch('/api/stats')
        ]);

        const leads = await leadsRes.json();
        const stats = await statsRes.json();

        updateStats(stats);
        updateTable(leads);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateStats(stats) {
    document.getElementById('total-leads').textContent = stats.total;
    document.getElementById('contacted-leads').textContent = stats.contacted;
    document.getElementById('new-leads').textContent = stats.new;
}

function updateTable(leads) {
    const tbody = document.getElementById('leads-body');
    tbody.innerHTML = '';

    if (leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No new leads found. The system is scanning for more...</td></tr>';
        return;
    }

    leads.forEach(lead => {
        const tr = document.createElement('tr');
        tr.dataset.id = lead.id;

        // Ensure consistent WhatsApp formatting: wa.me requires country code without + or 0
        let waPhone = lead.phone.replace(/[^0-9]/g, '');
        if (waPhone.startsWith('0')) {
            waPhone = '92' + waPhone.substring(1);
        }

        tr.innerHTML = `
            <td>${escapeHTML(lead.business_name)}</td>
            <td>${escapeHTML(lead.type)}</td>
            <td>${escapeHTML(lead.city)}</td>
            <td>${escapeHTML(lead.phone)}</td>
            <td>
                <button class="btn-whatsapp"
                    data-id="${lead.id}"
                    data-name="${escapeHTML(lead.business_name)}"
                    data-type="${escapeHTML(lead.type)}"
                    data-phone="${waPhone}">
                    Send WhatsApp
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function handleWhatsAppClick(e) {
    if (e.target.classList.contains('btn-whatsapp')) {
        const btn = e.target;
        const id = btn.getAttribute('data-id');
        const name = btn.getAttribute('data-name');
        const type = btn.getAttribute('data-type');
        const phone = btn.getAttribute('data-phone');

        // Prepare dynamic pitch
        let clients, action, focus;
        if (type === 'Clinic') {
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
        } else if (type === 'Store') {
            clients = 'Customers';
            action = 'buy products';
            focus = 'sales';
        } else {
            clients = 'Clients';
            action = 'book appointments';
            focus = 'services';
        }

        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const chatDay = new Date();
        chatDay.setDate(chatDay.getDate() + 2);
        const dayOfWeek = days[chatDay.getDay()];

        const pitch = `Hello ${name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${type} sector. Your establishment caught our attention due to its strong community presence! 🌟
*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${type} currently lacks a dedicated website.
*Your 24/7 Digital Partner 🕒*
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨
*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${type} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${type} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;

        const encodedPitch = encodeURIComponent(pitch);
        const waUrl = `https://wa.me/${phone}?text=${encodedPitch}`;

        // Optimistic UI Update
        const tr = btn.closest('tr');
        if (tr) tr.remove();

        // Update local stats optimistically
        const newLeadsEl = document.getElementById('new-leads');
        const contactedLeadsEl = document.getElementById('contacted-leads');
        if (newLeadsEl && contactedLeadsEl) {
            let currentNew = parseInt(newLeadsEl.textContent) || 0;
            let currentContacted = parseInt(contactedLeadsEl.textContent) || 0;
            if (currentNew > 0) newLeadsEl.textContent = currentNew - 1;
            contactedLeadsEl.textContent = currentContacted + 1;
        }

        // Open WhatsApp Link
        window.open(waUrl, '_blank');

        // Update Backend asynchronously
        fetch('/api/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: id })
        }).catch(err => console.error("Error updating contact status:", err));
    }
}

// Utility functions
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
