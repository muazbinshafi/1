import collector
import os

if os.path.exists('test.db'):
    os.remove('test.db')

collector.init_db('test.db')
collector.insert_lead('Test Clinic', 'Clinic', 'Bahawalpur', '0300-1234567', 'test.db')
leads = collector.get_uncontacted_leads('test.db')
print("Leads:", leads)
