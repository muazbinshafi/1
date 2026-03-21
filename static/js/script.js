document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchLeads();
    setInterval(fetchStats, 30000);
    setInterval(fetchLeads, 30000);
});

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('stat-total').textContent = data.total;
        document.getElementById('stat-contacted').textContent = data.contacted;
        document.getElementById('stat-new').textContent = data.new;
    } catch (err) {
        console.error('Error fetching stats:', err);
    }
}

async function fetchLeads() {
    try {
        const res = await fetch('/api/leads');
        const leads = await res.json();
        const tbody = document.getElementById('leads-body');

        tbody.innerHTML = leads.map(lead => `
            <tr data-id="${lead.id}">
                <td>${lead.business_name}</td>
                <td class="lead-type">${lead.type}</td>
                <td>${lead.city}</td>
                <td class="lead-phone">${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp">Send WhatsApp</button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error fetching leads:', err);
    }
}

document.addEventListener('click', async (e) => {
    if (e.target.classList.contains('btn-whatsapp')) {
        const row = e.target.closest('tr');
        const id = row.dataset.id;
        const businessName = row.children[0].textContent;
        const type = row.querySelector('.lead-type').textContent.toLowerCase();
        let phone = row.querySelector('.lead-phone').textContent;

        // Remove plus sign for wa.me link
        phone = phone.replace('+', '');

        let clients = "Clients";
        let action = "book appointments";
        let focus = "services";

        if (type === 'clinic') {
            clients = "Patients";
            action = "book appointments";
            focus = "care";
        } else if (type === 'store') {
            clients = "Customers";
            action = "buy products";
            focus = "sales";
        }

        const today = new Date();
        const chatDate = new Date(today);
        chatDate.setDate(today.getDate() + 2);
        const dayOfWeek = chatDate.toLocaleDateString('en-US', { weekday: 'long' });

        const message = `Hello ${businessName} 👋,
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

        const encodedMessage = encodeURIComponent(message);
        const whatsappUrl = `https://wa.me/${phone}?text=${encodedMessage}`;

        // Open WhatsApp
        window.open(whatsappUrl, '_blank');

        // Optimistic UI update
        row.remove();

        // Update backend
        try {
            await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ id: parseInt(id) })
            });
            fetchStats();
        } catch (err) {
            console.error('Error marking as contacted:', err);
        }
    }
});
