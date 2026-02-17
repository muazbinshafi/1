document.addEventListener('DOMContentLoaded', () => {
    const fetchBtn = document.getElementById('fetch-btn');
    const leadsBody = document.getElementById('leads-body');
    const emptyState = document.getElementById('empty-state');
    const totalLeadsEl = document.getElementById('total-leads');
    const contactedLeadsEl = document.getElementById('contacted-leads');

    fetchBtn.addEventListener('click', loadLeads);

    // Initial load
    updateAnalytics();
    loadLeads();

    async function loadLeads() {
        try {
            const response = await fetch('/api/leads');
            const leads = await response.json();
            renderLeads(leads);
            updateAnalytics();
        } catch (error) {
            console.error('Error fetching leads:', error);
        }
    }

    async function updateAnalytics() {
        try {
            const response = await fetch('/api/analytics');
            const data = await response.json();
            totalLeadsEl.textContent = data.total_leads; // Or leads.length + contacted
            contactedLeadsEl.textContent = data.contacted_leads;
        } catch (error) {
            console.error('Error fetching analytics:', error);
        }
    }

    function renderLeads(leads) {
        leadsBody.innerHTML = '';
        if (leads.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }
        emptyState.classList.add('hidden');

        leads.forEach(lead => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${lead.name}</td>
                <td><span class="badge ${lead.type.toLowerCase()}">${lead.type}</span></td>
                <td>${lead.city}</td>
                <td>${lead.phone}</td>
                <td>
                    <button class="btn whatsapp-btn" onclick="handleContact(${lead.id}, '${lead.phone}', '${lead.name}', '${lead.type}')">
                        Send WhatsApp
                        <span class="icon">➤</span>
                    </button>
                </td>
            `;
            leadsBody.appendChild(row);
        });
    }

    window.handleContact = async (id, phone, name, type) => {
        const message = generateWhatsAppMessage(name, type);
        const encodedMessage = encodeURIComponent(message);

        // Open WhatsApp
        const waUrl = `https://wa.me/${phone.replace(/\+/g, '')}?text=${encodedMessage}`;
        window.open(waUrl, '_blank');

        // Mark as contacted in backend
        try {
            await fetch(`/api/leads/${id}/contact`, { method: 'POST' });
            // Refresh list to remove the lead
            loadLeads();
        } catch (error) {
            console.error('Error marking lead as contacted:', error);
        }
    };

    function generateWhatsAppMessage(businessName, type) {
        const terminology = {
            "Clinic": {
                Sector: "Healthcare",
                Entity: "Clinic",
                Clients: "Patients",
                Action: "book appointments",
                Focus: "care"
            },
            "Store": {
                Sector: "Retail",
                Entity: "Store",
                Clients: "Customers",
                Action: "buy products",
                Focus: "sales"
            },
            "Service": {
                Sector: "Service",
                Entity: "Service",
                Clients: "Clients",
                Action: "book appointments",
                Focus: "services"
            }
        };

        const term = terminology[type] || terminology["Service"]; // Fallback to Service
        const dayOfWeek = getNextWeekday();

        return `Hello ${businessName} 👋,
This is MuazBinShafi, Owner of Business Solutions 🏢.
I hope this message finds you well. I’m reaching out because my team and I have been analyzing prominent businesses within the ${term.Sector} sector. Your establishment caught our attention due to its strong community presence! 🌟
**The Digital Opportunity 📈**
In our research, we noticed that many businesses like yours are thriving with an online presence, while your ${term.Entity} currently lacks a dedicated website.
**Your 24/7 Digital Partner 🕒**
In today’s digital world, a website acts as your most reliable assistant—it’s available 24/7 to help ${term.Clients} discover your services and ${term.Action} while you focus on ${term.Focus}. 💻✨
**Why Business Solutions?**
✅ **Competitive Advantage:** We specialize in creating platforms that outshine your competition.
🌐 **Digital Transformation:** We can elevate your ${term.Entity} to become a recognized 'Digital Brand.'
🛠️ **Comprehensive Service:** From design to hosting, we manage everything for you.
I would love to discuss how we can help your ${term.Entity} thrive online. Are you available for a brief chat on ${dayOfWeek}? 📞
Best regards,
MuazBinShafi
Owner | Business Solutions 💼`;
    }

    function getNextWeekday() {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const today = new Date();
        let nextDay = new Date(today);
        nextDay.setDate(today.getDate() + 1);
        // If Sunday (0), move to Monday
        if (nextDay.getDay() === 0) {
            nextDay.setDate(nextDay.getDate() + 1);
        }
        return days[nextDay.getDay()];
    }
});
