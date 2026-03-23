import run
client = run.app.test_client()
res = client.get('/api/stats')
print(res.data)
