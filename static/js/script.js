document.addEventListener('DOMContentLoaded', () => {
    const leadsBody = document.getElementById('leads-body');
    const leadsCount = document.getElementById('leads-count');

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function fetchLeads() {
        try {
            const response = await fetch('/api/leads');
            const leads = await response.json();
            renderLeads(leads);
        } catch (error) {
            console.error('Error fetching leads:', error);
        }
    }

    function generatePitch(lead) {
        let clients = 'Clients';
        let action = 'book appointments';
        let focus = 'services';
        let sector = lead.type;

        if (lead.type === 'Clinic') {
            clients = 'Patients';
            action = 'book appointments';
            focus = 'care';
        } else if (lead.type === 'Store') {
            clients = 'Customers';
            action = 'buy products';
            focus = 'sales';
        }

        const today = new Date();
        const chatDate = new Date(today);
        chatDate.setDate(today.getDate() + 2);
        const dayOptions = { weekday: 'long' };
        const dayOfWeek = chatDate.toLocaleDateString('en-US', dayOptions);

        return `Hello ${lead.name} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${sector} sector. Your establishment caught our attention due to its strong community presence! 🌟

*The Digital Opportunity 📈*
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${lead.type} currently lacks a dedicated website.

*Your 24/7 Digital Partner 🕒*
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${clients} discover your services and ${action} while you focus on ${focus}. 💻✨

*Why Business Solutions?*
✅ *Competitive Advantage:* We specialize in creating platforms that outshine your competition.
🌐 *Digital Transformation:* We can elevate your ${lead.type} to become a recognized 'Digital Brand.'
🛠️ *Comprehensive Service:* From design to hosting, we manage everything for you.

I would love to discuss how we can help your ${lead.type} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞

Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
    }

    function renderLeads(leads) {
        leadsCount.textContent = leads.length;
        leadsBody.innerHTML = '';

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.dataset.id = lead.id;

            const sanitizedPhone = lead.phone.replace(/[-\s]/g, '').replace(/^0/, '92');
            const pitch = generatePitch(lead);
            const waUrl = `https://wa.me/${sanitizedPhone}?text=${encodeURIComponent(pitch)}`;

            tr.innerHTML = `
                <td>${escapeHTML(lead.name)}</td>
                <td>${escapeHTML(lead.type)}</td>
                <td>${escapeHTML(lead.city)}</td>
                <td>${escapeHTML(lead.phone)}</td>
                <td>
                    <button class="btn-whatsapp" data-wa-url="${waUrl}">Send WhatsApp</button>
                </td>
            `;
            leadsBody.appendChild(tr);
        });
    }

    leadsBody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const waUrl = btn.dataset.waUrl;
            const tr = btn.closest('tr');
            const leadId = tr.dataset.id;

            // Open WhatsApp immediately
            window.open(waUrl, '_blank');

            // Optimistic UI update
            tr.remove();
            leadsCount.textContent = parseInt(leadsCount.textContent) - 1;

            // Notify backend
            try {
                await fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: leadId })
                });
            } catch (error) {
                console.error('Error updating lead status:', error);
            }
        }
    });

    fetchLeads();
});
