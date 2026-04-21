import collector
collector.init_db('test_scraper.db')
collector.collect_leads('test_scraper.db')
leads = collector.get_uncontacted_leads('test_scraper.db')
print("Found leads:", len(leads))
