import requests

response = requests.get("http://127.0.0.1:8080/adv/1/", json= {"key": "value"}, headers={"token": "aaa"})

# response = requests.post("http://127.0.0.1:5000/advs/", json={"title": "test_title 55555 ", "desc": "description", "owner":"user1"},
#                       headers={"token": "aaa"})

# response = requests.patch("http://127.0.0.1:5000/advs/2", json={"title": "edit_title 55555", "desc": "edit description", "owner":"user1"},
#                         headers={"token": "aaa"})

#double trouble
# response = requests.post("http://127.0.0.1:5000/advs/",
#                          json={"title": "test_title",  "owner": "user1"},
#                          headers={"token": "aaa"})

# response = requests.get("http://127.0.0.1:5000/advs/2")

#response = requests.delete("http://127.0.0.1:5000/advs/3")

print(response.status_code)
print(response.text)
