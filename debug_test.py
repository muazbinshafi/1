import run
client = run.app.test_client()
res = client.get('/api/leads')
print(res.data)
