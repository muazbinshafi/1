document.addEventListener('DOMContentLoaded', () => {
    const leadsBody = document.getElementById('leads-body');
    const statTotal = document.getElementById('stat-total');
    const statNew = document.getElementById('stat-new');
    const statContacted = document.getElementById('stat-contacted');

    const API_LEADS_URL = '/api/leads';
    const API_STATS_URL = '/api/stats';
    const API_CONTACT_URL = '/api/contact';

    // Fetch and display data
    async function fetchData() {
        try {
            const [leadsRes, statsRes] = await Promise.all([
                fetch(API_LEADS_URL),
                fetch(API_STATS_URL)
            ]);

            if (leadsRes.ok && statsRes.ok) {
                const leads = await leadsRes.json();
                const stats = await statsRes.json();

                updateStats(stats);
                renderLeads(leads);
            } else {
                console.error("Failed to fetch data.");
            }
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }

    // Update stats UI
    function updateStats(stats) {
        statTotal.textContent = stats.total;
        statNew.textContent = stats.new;
        statContacted.textContent = stats.contacted;
    }

    // Render table rows
    function renderLeads(leads) {
        leadsBody.innerHTML = '';

        if (leads.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="5" style="text-align: center;">No new leads available. Searching...</td>`;
            leadsBody.appendChild(tr);
            return;
        }

        leads.forEach(lead => {
            const tr = document.createElement('tr');
            tr.dataset.id = lead.id;

            tr.innerHTML = `
                <td>${lead.business_name}</td>
                <td>${lead.type}</td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn-whatsapp" data-id="${lead.id}" data-name="${lead.business_name}" data-type="${lead.type}" data-phone="${lead.phone}">
                        Send WhatsApp
                    </button>
                </td>
            `;
            leadsBody.appendChild(tr);
        });
    }

    // Generate WhatsApp Message
    function getWhatsAppMessage(name, type) {
        const typeLower = type.toLowerCase();
        let sector = "Business";
        let entity = "Business";
        let clients = "Customers";
        let action = "purchase products";
        let focus = "operations";

        if (typeLower.includes('clinic')) {
            sector = "Healthcare";
            entity = "Clinic";
            clients = "Patients";
            action = "book appointments";
            focus = "care";
        } else if (typeLower.includes('store')) {
            sector = "Retail";
            entity = "Store";
            clients = "Customers";
            action = "browse products";
            focus = "sales";
        } else if (typeLower.includes('service')) {
            sector = "Services";
            entity = "Service";
            clients = "Clients";
            action = "book appointments";
            focus = "services";
        }

        // Calculate day 2 days from now
        const date = new Date();
        date.setDate(date.getDate() + 2);
        const dayOfWeek = date.toLocaleDateString('en-US', { weekday: 'long' });

        return `Hello ${name} 👋,
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

    // Handle "Send WhatsApp" button click using event delegation
    leadsBody.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-whatsapp')) {
            const btn = e.target;
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const type = btn.getAttribute('data-type');
            let phone = btn.getAttribute('data-phone');

            // Format phone number for wa.me
            // Remove non-numeric characters, ensure it starts with country code if not 0
            phone = phone.replace(/[^\d+]/g, '');
            if (phone.startsWith('0')) {
                phone = '92' + phone.substring(1); // Assuming Pakistan country code for local numbers
            } else if (phone.startsWith('+')) {
                phone = phone.substring(1);
            }

            const message = getWhatsAppMessage(name, type);
            const encodedMessage = encodeURIComponent(message);
            const waUrl = `https://wa.me/${phone}?text=${encodedMessage}`;

            // 1. Open WhatsApp synchronously to avoid popup blockers
            window.open(waUrl, '_blank');

            // 2. Optimistic UI Update: hide the row
            const row = btn.closest('tr');
            if (row) {
                row.style.display = 'none';
            }

            // 3. Mark as contacted in backend
            try {
                const response = await fetch(API_CONTACT_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ id: id })
                });

                if (response.ok) {
                    // Update stats directly or let polling handle it
                    const currentNew = parseInt(statNew.textContent, 10);
                    const currentContacted = parseInt(statContacted.textContent, 10);
                    if (!isNaN(currentNew) && currentNew > 0) {
                        statNew.textContent = currentNew - 1;
                        statContacted.textContent = currentContacted + 1;
                    }
                } else {
                    console.error("Failed to mark lead as contacted on backend.");
                    // Revert optimistic UI if failed
                    if (row) {
                        row.style.display = '';
                    }
                }
            } catch (error) {
                console.error("Error communicating with backend:", error);
                // Revert optimistic UI
                if (row) {
                    row.style.display = '';
                }
            }
        }
    });

    // Initial fetch
    fetchData();

    // Poll every 30 seconds
    setInterval(fetchData, 30000);
});
