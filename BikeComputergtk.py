import gi
import os
import threading
import time
import subprocess
import math
import gtk
from gps import *
gi.require_version("Gtk", "3.0")
from pulsesensor import Pulsesensor
from flask import Flask
import logging
from gi.repository import Gtk, GObject, Gdk
GObject.threads_init()
gpsReport = ""
gpsSpeed = ""
gpsPos = ""
gpsDist = ""

class AlexaThread(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        
    def run(self):
        subprocess.call(['sudo', 'bash', 'startsample.sh'])
        subprocess.call(['sudo', 'h'])
        time.sleep(2)
        GObject.idle_add(self.callback)
        

class BikeComputer(object):
    
    def __init__(self):
        super(BikeComputer, self).__init__()
        #Window
        self.gladefile = "bikecomputer.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.gladefile)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1")
        #Variables
        self.speedVal = 0.0
        self.dist = 0.0
        self.odometer = 0.0
        self.bpmVal = 0.0
        self.tempVal = 0.0
        #Files
        self.file = open('odometer', 'r')
        #Layout Fields
        self.speed = self.builder.get_object("speed")
        self.avgSpeed = self.builder.get_object("avg_speed")
        self.bpmText = self.builder.get_object("bpm")
        self.temp = self.builder.get_object("temp")
        self.mediaAlert = self.builder.get_object("media_alert")
        self.locAlert = self.builder.get_object("loc_alert")
        self.miles = self.builder.get_object("miles")
        self.milesTrip = self.builder.get_object("trip_miles")
        self.button = self.builder.get_object("alexa_button")
        self.infoBar = self.builder.get_object("infoBar")
        self.infoLabel = self.builder.get_object("infoLabel")
        self.buttonDelete =  self.builder.get_object("button")
        self.messages = self.builder.get_object("messages")
        
        #Threads
        #self.threadAlexa = AlexaThread(self.work_finished_cb)
        #self.threadAlexa = threading.Thread(target=self.updateAlexa)
        self.threadGPS = threading.Thread(target=self.updateSpeed)
        self.threadBPM = threading.Thread(target=self.updateBPM)
        self.threadTemp = threading.Thread(target=self.updateTemp)
        #self.threadAlexa.start()        
        self.threadGPS.start()
        self.threadBPM.start()
        self.threadTemp.start()
        
        self.window.show()
    
    def on_gtk_quit_activate(self, object, data = None):
        self.window.connect("delete-event", Gtk.main_quit)
        
    def on_alexaButton_clicked(self, button, data=None):
        subprocess.call(['sudo', 'h'])
        self.button.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(15535, 33535, 65535))
        
    def work_finished_cb(self):
        self.messages.set_label("Alexa is Idle")
        self.messages.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 13535, 15535))
    
    def on_delete_clicked(self, buttonDelete, data=None):
        self.messages.set_text("-")
        
    def work_finished_cb2(self):
        self.locAlert.set_text("ONLINE")
        
    def updateAlexa(self):
        subprocess.call(['sudo', 'bash', 'startsample.sh'])
        subprocess.call(['sudo', 't'])
        
    def updateSpeed(self):
        subprocess.call(['ls', '/dev/ttyUSB*'])
        subprocess.call(['sudo', 'gpsd', '/dev/ttyUSB0', '-F', '/var/run/gpsd.sock'])
        subprocess.call(['cgps'])
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
        print('latitude\tlongitude\ttime utc\t\t\taltitude\tepv\tept\tspeed\tclimb') # '\t' = TAB to try and output the data in columns.
        
        def getDistance(oldLat, oldLong, latNow, longNow):
            # Haversine Formula
            R = 6371
            dLat = math.radians(float(latNow) - float(oldLat))
            dLon = math.radians(float(longNow) - float(oldLong))
            oldLat = math.radians(float(oldLat))
            latNow = math.radians(float(latNow))

            a = math.sin(dLat/2) * math.sin(dLat/2) + \
                math.cos(oldLat) * math.cos(latNow) * math.sin(dLon/2) * math.sin(dLon/2)

            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

            d = R * c * 0.621371 # Converting km to miles

            return d
        
        try:
            while True:
                report = gpsd.next() #
                count = 0
                if report['class'] == 'TPV':
                    oldLat = getattr(report,'lat',0.0)
                    oldLong = getattr(report,'lon',0.0)
                    self.speedVal = getattr(report,'speed','nan')
                    time.sleep(1)
                    count += 1
                    latNow = getattr(report,'lat',0.0)
                    longNow = getattr(report,'lon',0.0)
                                        
                    self.speed.set_text(str(self.speedVal))
                    self.dist = getDistance(oldLat, oldLong, latNow, longNow)
                    self.milesTrip.set_text(str(self.dist) + " mi. trip")
                    self.file = open("odometer", "r")
                    distDiff = int(self.file.read())
                    self.odometer = distDiff + int(self.dist)
                    print("Odo: " + str(self.odometer))
                    self.file = open("odometer", "w")
                    self.file.write(str(self.odometer))
                    self.miles.set_text(str(self.odometer) + " mi.")
                    self.avgSpeed.set_text(str(self.dist / count))
                    self.locAlert.set_text("Climb: " + getattr(report, 'climb', 'nan') + "\nAlt: " + getattr(report, 'alt', 'nan') + "\nLat/Long: " + getattr(report, 'lat', 'nan') + ":" + getattr(report, 'lon', 'nan"))
                
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            print("Done.\nExiting.")
    
    def updateBPM(self):
        self.bpmText.set_text("Test")
        p = Pulsesensor()
        p.startAsyncBPM()

        try:
            while True:
                bpm = p.BPM
                self.bpmText.set_text(str(int(bpm)) + " bpm")
                if bpm > 0:
                    if bpm > 150:
                        self.bpmText.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 13535, 15535))
                        self.messages.set_text("HIGH HEARTRATE")
                    elif bpm > 90:
                        self.bpmText.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(65535, 33535, 15535))
                    else:
                        self.bpmText.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(0, 0, 0))
                else:
                    self.bpmText.set_text("-")
                time.sleep(1)
        except:
            p.stopAsyncBPM()
            
    def updateTemp(self):
        self.temp.set_text("Test") 
    
    def on_window1_destroy(self, object, data=None):
        self.window.connect("delete-event", Gtk.main_quit)

if __name__ == "__main__":
    main = BikeComputer()
    Gtk.main()
 