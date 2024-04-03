# smartmirror.py
# requirements
# requests, feedparser, traceback, Pillow

# from tkinter import *
import tkinter
from tkinter import *
import locale
import threading
import time
import requests
import json
import traceback
import feedparser
from tkinter import Label, Button, Entry  # Ensure to import specific widget types you're using

from PIL import Image, ImageTk
from contextlib import contextmanager

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os.path

import serial


LOCALE_LOCK = threading.Lock()

ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 12 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
news_country_code = 'us'
# weather_api_token = '<TOKEN>' # create account at https://darksky.net/dev/
weather_api_token = '<TOKEN>' # create account at https://darksky.net/dev/
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = None # Set this if IP location lookup does not work for you (must be a string)
longitude = None # Set this if IP location lookup does not work for you (must be a string)
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18
#small_text_size = 12

#root = tkinter.Tk()
#root.attributes('-fullscreen', True)  # Set the window to full-screen mode

# label = tkinter.Label(root, text="Hello, Tkinter!")
# label.pack()  # Make sure this line is present

@contextmanager
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    'clear-day': "assets/Sun.png",  # clear sky day
    'wind': "assets/Wind.png",   #wind
    'cloudy': "assets/Cloud.png",  # cloudy day
    'partly-cloudy-day': "assets/PartlySunny.png",  # partly cloudy day
    'rain': "assets/Rain.png",  # rain day
    'snow': "assets/Snow.png",  # snow day
    'snow-thin': "assets/Snow.png",  # sleet day
    'fog': "assets/Haze.png",  # fog day
    'clear-night': "assets/Moon.png",  # clear sky night
    'partly-cloudy-night': "assets/PartlyMoon.png",  # scattered clouds night
    'thunderstorm': "assets/Storm.png",  # thunderstorm
    'tornado': "assests/Tornado.png",    # tornado
    'hail': "assests/Hail.png"  # hail
}


# Function to make text invisible for supported widgets
def make_text_invisible():
    print("Making text invisible!!!!")
    for widget in root.winfo_children():
        # Apply only to widgets that support text or foreground color change
        if isinstance(widget, (Label, Button, Entry)):
            try:
                 widget.config(foreground="black")  # Assuming black is your background color
            except tkinter.TclError as e:
                 print(f"Error updating widget: {e}")
        widget.pack_forget()  # Hide the widget

# Function to make text visible for supported widgets
def make_text_visible():
    for widget in root.winfo_children():
        if isinstance(widget, (Label, Button, Entry)):
            try:
                widget.config(foreground="white")  # Change to your desired text color
            except tkinter.TclError as e:
                print(f"Error updating widget: {e}")
        widget.pack() 


class Reminders(Frame):
    def __init__(self, parent, *args, **kwargs):
        # Frame.__init__(self, parent, *args, **kwargs)
        super().__init__(parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'Reminders'
        self.remindersLbl = Label(self, text=self.title, font=('Avenir', medium_text_size), fg="white", bg="black")
        self.remindersLbl.pack(side=TOP, anchor=W)
        self.remindersContainer = Frame(self, bg="black")
        self.remindersContainer.pack(side=TOP)
        self.reminderWidgets = []  # Keep track of reminder widgets
        self.reminderTitles = []  # New list to keep track of the titles
        self.get_reminders()

    def get_reminders(self):
        # Authentication and building the service
        SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('tasks', 'v1', credentials=creds)

        # # Clear existing reminders from the display
        # for widget in self.remindersContainer.winfo_children():
        #     widget.destroy()

        # Call the Tasks API
        results = service.tasks().list(tasklist='@default', maxResults=2).execute()
        items = results.get('items', [])

        new_titles = [item['title'] for item in items]  # Extract titles from fetched items

        # Update or create widgets based on new titles
        for i, title in enumerate(new_titles):
            if i < len(self.reminderWidgets):
                if self.reminderTitles[i] != title:
                    # Update widget text only if it has changed
                    self.reminderWidgets[i].config(text=title)
                    self.reminderTitles[i] = title  # Update the title being displayed
            else:
                # Create new reminder widget if more titles than widgets
                reminder = Label(self.remindersContainer, text=title, font=('Avenir', small_text_size), fg="white", bg="black")
                reminder.pack(side=TOP, anchor=W)
                self.reminderWidgets.append(reminder)  # Add widget to the list
                self.reminderTitles.append(title)  # Add title to the list

        # Hide any excess widgets if there are fewer new titles than widgets
        for j in range(len(new_titles), len(self.reminderWidgets)):
            self.reminderWidgets[j].pack_forget()
            self.reminderTitles[j] = ""  # Clear the title for hidden widgets

        # self.after(600000, self.get_reminders)  # Refresh every 10 minutes
        self.after(600, self.get_reminders)  # Refresh every 10 minutes
        # print("Refreshed reminders")

class Reminder(Frame):
    def __init__(self, parent, reminder_text=""):
        Frame.__init__(self, parent, bg='black')
        self.reminderText = reminder_text
        self.reminderLbl = Label(self, text=self.reminderText, font=('Avenir', small_text_size), fg="white", bg="black")
        self.reminderLbl.pack(side=LEFT, anchor=N)

class Dance(Frame):
    def __init__(self, parent, reminder_text=""):
        Frame.__init__(self, parent, bg='black')
        # Initialize label for "Recording Dance" text
        self.recording_label = Label(self, text="Recording Dance", font=('Avenir', large_text_size), fg="white", bg="black")
        self.recording_label.place(relx=0.5, rely=0.5, anchor=CENTER)
        

class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Avenir', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Avenir', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Avenir', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)

       # Add a button for recording dance
        #self.recordButton = Button(self, text="Record my dance!!!", command=self.record_dance, font=('Avenir', small_text_size), fg="white", bg="black")
        #self.recordButton.pack(side=TOP, anchor=E, pady=10)  # Add some padding to separate from the date

        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)

    def record_dance(self):
        # Placeholder for the actual recording functionality
        # Initialize label for "Recording Dance" text
        #self.recording_label = Label(self.tk, text="Recording Dance", font=('Avenir', large_text_size), fg="white", bg="black")
        #self.recording_label.place(relx=0.5, rely=0.5, anchor=CENTER)
        #self.recording_label.pack_forget()  # Hide the label initially
        print("Recording the dance!")
        # make_text_invisible()


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Avenir', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black")
        self.iconLbl.pack(side=LEFT, anchor=N, padx=20)
        self.currentlyLbl = Label(self, font=('Avenir', medium_text_size), fg="white", bg="black")
        self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Avenir', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)
        self.locationLbl = Label(self, font=('Avenir', small_text_size), fg="white", bg="black")
        self.locationLbl.pack(side=TOP, anchor=W)
        # self.get_weather()

    def get_ip(self):
        try:
            ip_url = "http://jsonip.com/"
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return ("Error: %s. Cannot get ip." % e)

    def get_weather(self):
        try:

            if latitude is None and longitude is None:
                # get location
                location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj['latitude']
                lon = location_obj['longitude']

                location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
            else:
                location2 = ""
                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign= u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]

            icon_id = weather_obj['currently']['icon']
            icon2 = None

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((100, 100), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.iconLbl.config(image=photo)
                    self.iconLbl.image = photo
            else:
                # remove image
                self.iconLbl.config(image='')

            if self.currently != currently2:
                self.currently = currently2
                self.currentlyLbl.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)
            if self.location != location2:
                if location2 == ", ":
                    self.location = "Cannot Pinpoint Location"
                    self.locationLbl.config(text="Cannot Pinpoint Location")
                else:
                    self.location = location2
                    self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
            print ("Error: %s. Cannot get weather." % e)

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32

class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News' # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Avenir', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
            if news_country_code == None:
                headlines_url = "https://news.google.com/news?ned=us&output=rss"
            else:
                headlines_url = "https://news.google.com/news?ned=%s&output=rss" % news_country_code

            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:5]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print("Error: %s. Cannot get news." % e)

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Avenir', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)


class Calendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Calendar Events'
        self.calendarLbl = Label(self, text=self.title, font=('Avenir', medium_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side=TOP, anchor=E)
        self.calendarEventContainer = Frame(self, bg='black')
        self.calendarEventContainer.pack(side=TOP, anchor=E)
        self.get_events()

    def get_events(self):
        #TODO: implement this method
        # reference https://developers.google.com/google-apps/calendar/quickstart/python

        # remove all children
        for widget in self.calendarEventContainer.winfo_children():
            widget.destroy()

        calendar_event = CalendarEvent(self.calendarEventContainer)
        calendar_event.pack(side=TOP, anchor=E)
        pass


class CalendarEvent(Frame):
    def __init__(self, parent, event_name="Event 1"):
        Frame.__init__(self, parent, bg='black')
        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Avenir', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=E)


class FullscreenWindow:

    def __init__(self):
        # self.tk = Tk()
        self.tk = root
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES,  padx=100, pady=250, anchor=SW)
        self.state = False
        self.tk.attributes("-fullscreen", True)  # Start in fullscreen mode
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
        # weather
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        # news
        # UNCOMMENTING!!
        # self.news = News(self.bottomFrame)
        # self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)

        # Call the function to make text invisible
        # make_text_invisible()

        self.reminders = Reminders(self.bottomFrame)
        self.reminders.pack(side=LEFT, anchor=S, padx=100, pady=200)
        
        self.recording_label = Dance(self.bottomFrame)
        self.recording_label.pack_forget()  # Hide the label initially

        # calender - removing for now
        # self.calender = Calendar(self.bottomFrame)
        # self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

# Add an exit method
def exit(event):
    root.destroy()

if __name__ == '__main__':

    #make_text_invisible()
    # Device 00:21:13:05:F0:64 HC-06
    # ls /dev/rfcomm0
    
    # Replace '/dev/rfcomm0' with the correct path to your HC-06 Bluetooth device
    serial_port = serial.Serial('/dev/rfcomm0', baudrate=9600, timeout=1)

    pir = 0
    ir = 0

    root = tkinter.Tk()
    # Bind the escape key to exit full-screen mode and close the application
    root.bind('<Button-3>', exit)
    w = FullscreenWindow()
    w.tk.mainloop()

    try:
        while True:
            # Read data from the HC-06 Bluetooth module
            data = serial_port.readline().decode().strip()
            
            # Parse the received data
            if data.startswith('p') and ' ' in data:
                p_index = data.index(' ')
                pir_str = data[1:p_index]
                if pir_str.isdigit():
                    pir = int(pir_str)
                if 'i' in data:
                    ir_str = data[data.index('i')+1:]
                    if ir_str.isdigit():
                        ir = int(ir_str)
            
            # Toggle reminders based on ir value
            if ir == 1:
                w.reminders.pack_forget()  # Hide reminders
                w.recording_label.pack(relx=0.5, rely=0.5, anchor=CENTER)
            else:
                w.reminders.pack(side=LEFT, anchor=S, padx=100, pady=100)  # Show reminders
                w.recording_label.pack_forget()
                
            # Make all text invisible when pir == 0
            if pir == 0:
                make_text_invisible()
            else:
                make_text_visible()
                
            # Print the received data to verify
            print("PIR:", pir, "IR:", ir)

    finally:
        # Close the serial port when done
        serial_port.close()
        exit(0)




