document.addEventListener('DOMContentLoaded', () => {
    const leadsTableBody = document.getElementById('leads-table-body');
    const totalLeadsEl = document.getElementById('total-leads');
    const newLeadsEl = document.getElementById('new-leads');
    const contactedLeadsEl = document.getElementById('contacted-leads');

    // Polling intervals
    const POLL_INTERVAL = 30000; // 30 seconds

    function fetchStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                totalLeadsEl.textContent = data.total;
                newLeadsEl.textContent = data.new;
                contactedLeadsEl.textContent = data.contacted;
            })
            .catch(error => console.error('Error fetching stats:', error));
    }

    function fetchLeads() {
        fetch('/api/leads')
            .then(response => response.json())
            .then(data => {
                renderLeads(data);
            })
            .catch(error => console.error('Error fetching leads:', error));
    }

    function renderLeads(leads) {
        leadsTableBody.innerHTML = '';
        if (leads.length === 0) {
            leadsTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No active leads available at the moment.</td></tr>';
            return;
        }

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${lead.business_name}</td>
                <td>${lead.type}</td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp"
                            data-id="${lead.id}"
                            data-name="${lead.business_name}"
                            data-type="${lead.type}"
                            data-phone="${lead.phone}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            leadsTableBody.appendChild(tr);
        });
    }

    function generatePitch(name, type) {
        // Default terminology
        let sector = type;
        let entity = type.toLowerCase();
        let clients = "Clients";
        let action = "book appointments";
        let focus = "services";

        if (type === "Clinic") {
            sector = "Healthcare";
            clients = "Patients";
            action = "book appointments";
            focus = "care";
        } else if (type === "Store") {
            sector = "Retail";
            clients = "Customers";
            action = "buy products";
            focus = "sales";
        } else if (type === "Service") {
            sector = "Services";
            clients = "Clients";
            action = "book appointments";
            focus = "services";
        }

        const date = new Date();
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        // Pick a day 2 days from now for the chat
        const dayOfWeek = days[(date.getDay() + 2) % 7];

        const pitch = `Hello ${name} 👋,

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

        return encodeURIComponent(pitch);
    }

    // Event Delegation for "Send WhatsApp"
    leadsTableBody.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            let phone = btn.getAttribute('data-phone');

            // Format phone number for wa.me (remove +, spaces, etc if necessary)
            phone = phone.replace(/\D/g, '');

            const pitch = generatePitch(name, type);
            const waUrl = `https://wa.me/${phone}?text=${pitch}`;

            // Synchronous open to prevent popup blocking
            window.open(waUrl, '_blank');

            // Asynchronous backend update
            fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: id })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    // Instantly remove row from UI for snappy feedback
                    btn.closest('tr').remove();
                    fetchStats(); // Update stats immediately
                }
            })
            .catch(error => console.error('Error updating lead status:', error));
        }
    });

    // Initial fetch
    fetchStats();
    fetchLeads();

    // Polling
    setInterval(() => {
        fetchStats();
        fetchLeads();
    }, POLL_INTERVAL);
});