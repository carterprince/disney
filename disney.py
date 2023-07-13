import requests
import json
import smtplib
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pyshorteners

with open("config.json") as f:
    config = f.read()

# remove lines that start with //
config_text = "\n".join([line for line in config.split("\n") if not line.strip().startswith("//")])
config = json.loads(config_text)
if config["logging"]:
    print(config_text)

emailadmin = config["emailadmin"]
password = config["password"]

def send_email(email, msg):
    # create a message
    message = MIMEMultipart()
    message["From"] = config["emailadmin"]
    message["To"] = email
    message["Subject"] = "Reservation Available"
    message.attach(MIMEText(msg, "plain"))

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(emailadmin, password)
    server.send_message(message)
    server.quit()

def shorten_url(url):
    s = pyshorteners.Shortener()
    return s.tinyurl.short(url)

headers = {
    'authority': 'disneyworld.disney.go.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

# Create an empty list to track notifications
notified_reservations = []

def get_availability():
    for date in config["dates"]:
        for time in config["times"]:
            for restaurant in config["restaurants"]:
                for party_size in config["partySizes"]:
                    url = f"https://disneyworld.disney.go.com/finder/api/v1/explorer-service/dining-availability/%7BC032915C-ACF2-4389-B291-5CACF273897E%7D/wdw/{config['restaurants'][restaurant]['id']};entityType=restaurant/table-service/{party_size}/{date}/?mealPeriod={config['times'][time]}"
                    response = requests.get(url, headers=headers)
                    data = response.json()
                    if config["logging"]: print(data)
                    if "unavailableReason" in data:
                        msg = f"{restaurant} ({date}, {time}) for {party_size} is unavailable"
                    else:
                        offers = data["offers"]
                        restaurantURL = config["restaurants"][restaurant]["url"]
                        restaurantURL = shorten_url(restaurantURL)
                        msg = f"{restaurant} ({date}, {time}) for {party_size} is available at {restaurantURL}"
                        
                        # Generate a unique key for this reservation
                        reservation_key = f"{restaurant}_{date}_{time}_{party_size}"
                        
                        # Only send an email if we haven't notified about this reservation yet
                        if reservation_key not in notified_reservations:
                            for recipient in config["recipients"]:
                                send_email(config["recipients"][recipient], msg)
                            print("Email sent")
                            
                            # Add this reservation to the notified list
                            notified_reservations.append(reservation_key)
                    print(msg)
                    sleep(config["betweenRequestDelay"])

while True:
    get_availability()
    sleep(config["sleepAfterDelay"])
