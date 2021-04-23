import requests
import threading

def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        func()

        
def ping_geo():
    response = requests.get("http://169.226.181.187:7006/ping_geo")
    print(response.json())
    
def ping_gust():
    response = requests.get("http://169.226.181.187:7006/ping_gust")
    print(response.json())
    
    
def execute():
    ping_geo()
    ping_gust()

execute()
setInterval(execute,60*30)