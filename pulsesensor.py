import time
import threading
from MCP3008 import MCP3008

class Pulsesensor:
    def __init__(self, channel = 0, bus = 0, device = 0):
        self.channel = channel
        self.BPM = 0
        self.adc = MCP3008(bus, device)

    def getBPMLoop(self):
        # init variables
        rate = [0] * 10         # array to hold last 10 IBI values
        sampleCounter = 0       # used to determine pulse timing
        lastBeatTime = 0        
        P = 512                 # peak in pulse wave
        T = 512                 # trough in pulse wave
        thresh = 525            # instant moment of heart beat
        amp = 100               # amplitude of pulse waveform
        firstBeat = True        
        secondBeat = False      

        IBI = 600               # time interval between beats
        Pulse = False           # "True" heartbeat is detected
        lastTime = int(time.time()*1000)
        
        while not self.thread.stopped:
            Signal = self.adc.read(self.channel)
            currentTime = int(time.time()*1000)
            
            sampleCounter += currentTime - lastTime
            lastTime = currentTime
            
            N = sampleCounter - lastBeatTime

            # find the peak and trough of the pulse wave
            if Signal < thresh and N > (IBI/5.0)*3:     # avoid dichrotic noise by waiting 3/5 of last IBI
                if Signal < T:                          
                    T = Signal                          # keep track of lowest point in pulse wave 

            if Signal > thresh and Signal > P:
                P = Signal

            # signal surges up in value every time there is a pulse
            if N > 250:                                 # avoid noise
                if Signal > thresh and Pulse == False and N > (IBI/5.0)*3:       
                    Pulse = True                        
                    IBI = sampleCounter - lastBeatTime  # measure time between beats
                    lastBeatTime = sampleCounter        # keep track of time for next pulse

                    if secondBeat:                      # if secondBeat == TRUE
                        secondBeat = False;             # clear secondBeat flag
                        for i in range(len(rate)):      # seed the running total to get a realisitic BPM at startup
                          rate[i] = IBI

                    if firstBeat:                       # if firstBeat == TRUE
                        firstBeat = False;              # clear firstBeat flag
                        secondBeat = True;              # set the second beat flag
                        continue

                    # keep a running total of the last 10 IBI values  
                    rate[:-1] = rate[1:]                # shift data in the rate array
                    rate[-1] = IBI                      
                    runningTotal = sum(rate)            # add upp oldest values

                    runningTotal /= len(rate)           # average the values 
                    self.BPM = 60000/runningTotal       # how many beats fit into a minute

            if Signal < thresh and Pulse == True:       # when the values are going down, the beat is over
                Pulse = False                           # reset the Pulse flag
                amp = P - T                             # get amplitude of the pulse wave
                thresh = amp/2 + T                      # set thresh at 50% of the amplitude
                P = thresh                              
                T = thresh

            if N > 2500:                                # if 2.5 seconds go by without a beat
                thresh = 512                            # set thresh default
                P = 512                                 # set P default
                T = 512                                 # set T default
                lastBeatTime = sampleCounter            # bring the lastBeatTime up to date        
                firstBeat = True                        # set these to avoid noise
                secondBeat = False                      
                self.BPM = 0

            time.sleep(0.005)
            
        
    # Start getBPMLoop routine which saves the BPM in its variable
    def startAsyncBPM(self):
        self.thread = threading.Thread(target=self.getBPMLoop)
        self.thread.stopped = False
        self.thread.start()
        return
        
    # Stop the routine
    def stopAsyncBPM(self):
        self.thread.stopped = True
        self.BPM = 0
        return
    
