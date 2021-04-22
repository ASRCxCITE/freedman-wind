import requests
import threading

def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        func()

        
def ping_api():
    response = requests.get("http://169.226.181.187:7006/ping")
    print(response)
    
ping_api()
setInterval(ping_api,60*30)