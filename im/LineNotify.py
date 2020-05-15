# -*- coding: UTF-8 -*-
import requests, os
 
class LineNotify():
    def __init__(self, token):
        self.token = token

    def send(self, msg, picURI=None):
        url = "https://notify-api.line.me/api/notify"
        headers = {
            "Authorization": "Bearer " + self.token
        }
   
        payload = {'message': msg}
        files = {'imageFile': open(picURI, 'rb')}
        r = requests.post(url, headers = headers, params = payload, files = files)
        return r.status_code
 
#token = os.environ["LINE_TEST_TOKEN"]
#msg = "Hello Python"
#picURI = "/data/data/com.termux/files/home/girlfriend.jpg"

if __name__ == "__main__":
    token = 'BSwQXMJoXQvABhIdiTyLIDbe1cWL8DxlpFEaUcCZZWA'
    line = LineNotify(token)
    msg = "Hello Python"
    picURI = "D:/private/WorkArea/PhotoThisDay/res/.thumbnail/IMG_20200330_192704.jpg"
    print(line.send(msg,picURI))
