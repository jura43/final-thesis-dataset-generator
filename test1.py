import grequests
test = [grequests.get('https://google.com')]
rs = grequests.map(test)
print(rs[0].status_code)