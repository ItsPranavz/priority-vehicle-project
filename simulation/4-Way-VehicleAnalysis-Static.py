import argparse
import random
import math
import time
import threading
import os
import re
import pygame
import sys
import pandas as pd
import csv

# Default values of signal times
defaultRed = 132
defaultYellow = 3
defaultGreen = 20
defaultMinimum = 10
defaultMaximum = 60
# Define the default green signal duration in seconds (e.g., 30 seconds)
defaultGreenDuration = 30


data = []
trustScoreData = []
activePriorityVehicles = []
Emergency = False
displaySkip = False
signals = []
congestion = []
noOfSignals = 4
simTime = 400       # total simulation time
timeElapsed = 0

totalWaitTime = 0

weightage = 0.33
hotspot_region = False
traffic_distribution = []

# In[4]:


currentGreen = 0   # Indicates which signal is green

nextGreen = (currentGreen+1) % noOfSignals

currentYellow = 0   # Indicates whether yellow signal is on or off


# Average times for vehicles to pass the intersection
carTime = 1.5             # 50km/h
bikeTime = 1            # 60km/h
rickshawTime = 2          # 60km/h
busTime = 2.5            # 45km/h
truckTime = 2.5           # 45km/h
ambulanceTime = 1
fireTruckTime = 1
policeCarTime = 1

# In[5]:


# Count of vehicles at a traffic signal
noOfCars = 0
noOfBikes = 0
noOfBuses = 0
noOfTrucks = 0
noOfRickshaws = 0
noOfAmbulances = 0
noOffireTrucks = 0
noOfPoliceCars = 0
noOfLanes = 2
roadLanes = 3

speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8,
          'rickshaw': 2, 'bike': 2.5,
          'ambulance': 3, 'fireTruck': 3}  # average speeds of vehicles

# weather , congestion, 
weatherData = {
  
  'Thunderstorm': 0,
  'Drizzle': 0.3,
  'rain': 0.4,
  'Snow': 0.3,
  'Mist': 0.4,
  'Smoke': 0.2,
  'Haze': 0.3,
  'Fog': 0.2,
  'Sand': 0.1,
  'Dust': 0.1,
  'Tornado': 0,
  'clear sky': 1,
  'few clouds': 0.8,
  'Scattered clouds': 0.7,
  'Broken clouds': 0.5,
  'overcast clouds': 0.3

}


# In[7]:


# Coordinates of start
x = {'right': [-100, -100, -100], 'down': [750, 720, 692],
     'left': [1500, 1500, 1500], 'up': [602, 630, 661]}
y = {'right': [349, 375, 400], 'down': [-100, -100, -100],
     'left': [488, 458, 430], 'up': [900, 900, 900]}


# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]
vehicleCountCoods = [(480, 210), (880, 210), (880, 550), (480, 550)]
vehicleCountTexts = ["0", "0", "0", "0"]
trustDynamicCoords = [(30, 225), (810, 35), (1230, 555), (420, 675)]
trustHistoricCoords = [(30, 250), (810, 60), (1230, 580), (420, 700)]
trafficCongestionCoords = [(30,275),(810,85),(1120,605),(305,725)]
weatherDataCoords = [(30,300),(810,110),(1120,630),(305,750)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

stops = {'right': [580, 580, 580], 'down': [320, 320, 320],
         'left': [810, 810, 810], 'up': [545, 545, 545]}

firstStep = {'right': 430, 'down': 170, 'left': 950, 'up': 695}

secondStep = {'right': 280, 'down': 20, 'left': 1100, 'up': 845}


mid = {'right': {'x': 720, 'y': 445}, 'down': {'x': 695, 'y': 460},
       'left': {'x': 680, 'y': 425}, 'up': {'x': 695, 'y': 400}}
rotationAngle = 3

# Gap between vehicles
stoppingGap = 25    # stopping gap
movingGap = 25   # moving gap


# In[8]:


vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}

vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'rickshaw',
                4: 'bike', 5: 'ambulance', 6: 'fireTruck'}


directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}


# In[9]:


pygame.init()
simulation = pygame.sprite.Group()
pygame.mixer.init()
sound_file = "C:\\Users\\arnav_yi3dtrt\\OneDrive\\Desktop\\Ambulance Project\\Pygame Simulation\\Previous work\\images\\ambulance-siren.mp3"
pygame.mixer.music.load(sound_file)

# In[10]:


class TrafficSignal:
    def __init__(self, red, yellow, green, minimum=0, maximum=0):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.totalGreenTime = 0
        self.signalText = "---"
    


class TrustSignal:
    def __init__(self, src_lat, src_long, dest_lat, dest_long):
        self.congestion_time = ""
        self.congestion_score = 0.00
        self.weather_score = 0.00
        self.weather_description = ""
        self.hotspot_score = 0.00
        self.src_lat = src_lat
        self.src_long = src_long
        self.dest_lat = dest_lat
        self.dest_long = dest_long
        self.trust_dynamic = 0.00
        self.trust_static = 0.00

# In[11]:


class Vehicle(pygame.sprite.Sprite):

    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn,active=False):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.direction_number = direction_number
        self.active = active
        self.wait_time = 0
        self.direction = direction
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "..\\images\\" + direction + "\\" + vehicleClass + ".png" #adjust path acording to your device(images)
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        if(direction == 'right'):

            # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect(
                ).width - stoppingGap         # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap

            else:

                self.stop = defaultStop[direction]

            # Set new starting and stopping coordinate
            temp = self.currentImage.get_rect().width + stoppingGap
            # x[direction][lane] -= temp
            stops[direction][lane] -= temp

        elif(direction == 'left'):

            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop + \
                    vehicles[direction][lane][self.index - 1].currentImage.get_rect().width + stoppingGap

            else:
                self.stop = defaultStop[direction]

            temp = self.currentImage.get_rect().width + stoppingGap
            # x[direction][lane] += temp
            stops[direction][lane] += temp

        elif(direction == 'down'):

            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop - \
                    vehicles[direction][lane][self.index -
                                              1].currentImage.get_rect().height - stoppingGap

            else:
                self.stop = defaultStop[direction]

            temp = self.currentImage.get_rect().height + stoppingGap
            # y[direction][lane] -= temp
            stops[direction][lane] -= temp

        elif(direction == 'up'):

            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop + \
                    vehicles[direction][lane][self.index -
                                              1].currentImage.get_rect().height + stoppingGap

            else:
                self.stop = defaultStop[direction]

            temp = self.currentImage.get_rect().height + stoppingGap
            # y[direction][lane] += temp
            stops[direction][lane] += temp

        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):

        if(self.direction == 'right'):

            # if the image has crossed stop lines
            if(self.crossed == 0 and self.x+self.currentImage.get_rect().width > stopLines[self.direction]):

                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.x+self.currentImage.get_rect().width < stopLines[self.direction] + 40):

                        if((self.x+self.currentImage.get_rect().width <= self.stop or
                            (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and
                           (self.index == 0 or self.x+self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.x += self.speed

                    else:

                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x += 2.4
                            self.y -= 2.8
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or self.y-self.currentImage.get_rect().height
                               > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                               or self.x+self.currentImage.get_rect().width
                               < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)):

                                self.y -= self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.x+self.currentImage.get_rect().width < mid[self.direction]['x']):

                        if((self.x+self.currentImage.get_rect().width <= self.stop or
                            (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and
                           (self.index == 0 or self.x+self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.x += self.speed

                    else:

                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or self.y+self.currentImage.get_rect().height
                               < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                               or self.x+self.currentImage.get_rect().width
                               < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)):

                                self.y += self.speed

            else:
                if((self.x+self.currentImage.get_rect().width <= self.stop or self.crossed == 1 or
                    (currentGreen == 0 and currentYellow == 0)) and (self.index == 0 or
                                                                     self.x+self.currentImage.get_rect().width
                                                                     < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                                                                     or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x += self.speed  # move the vehicle

        elif(self.direction == 'down'):

            if(self.crossed == 0 and self.y+self.currentImage.get_rect().height > stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.y+self.currentImage.get_rect().height < stopLines[self.direction] + 50):

                        if((self.y+self.currentImage.get_rect().height <= self.stop
                            or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y+self.currentImage.get_rect().height
                           < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y += self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x += 1.2
                            self.y += 1.8
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                               or self.y < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)):
                                self.x += self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.y+self.currentImage.get_rect().height < mid[self.direction]['y']):

                        if((self.y+self.currentImage.get_rect().height <= self.stop
                            or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y+self.currentImage.get_rect().height
                           < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y += self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                               or self.y < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)):
                                self.x -= self.speed

            else:
                if((self.y+self.currentImage.get_rect().height <= self.stop or self.crossed == 1
                    or (currentGreen == 1 and currentYellow == 0))
                   and (self.index == 0 or self.y+self.currentImage.get_rect().height
                        < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                        or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    self.y += self.speed

        elif(self.direction == 'left'):

            if(self.crossed == 0 and self.x < stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.x > stopLines[self.direction] - 60):
                        if((self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):
                            self.x -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x -= 1
                            self.y += 1.2
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).height < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                               or self.x > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)):

                                self.y += self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.x > mid[self.direction]['x']):
                        if((self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):
                            self.x -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x -= 1.8
                            self.y -= 2.5
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                               or self.x > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)):

                                self.y -= self.speed

            else:
                if((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0))
                   and (self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                        or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x -= self.speed  # move the vehicle

        elif(self.direction == 'up'):

            if(self.crossed == 0 and self.y < stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.y > stopLines[self.direction] - 45):
                        if((self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x -= 2
                            self.y -= 1.5
                            if(self.rotateAngle == 90):
                                self.turned = 1
                        else:
                            if(self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                               or self.y > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)):
                                self.x -= self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.y > mid[self.direction]['y']):
                        if((self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if(self.rotateAngle == 90):
                                self.turned = 1
                        else:
                            if(self.index == 0 or self.x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                               or self.y > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)):
                                self.x += self.speed
            else:
                if((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0))
                   and (self.index == 0 or self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                        or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    self.y -= self.speed


# In[12]:


# # Initialization of signals with default values
# def initialize():

#     ts1 = TrafficSignal(0, defaultYellow, defaultMaximum,
#                         defaultMinimum, defaultMaximum)
    
#     signals.append(ts1)
#     ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow,
#                         defaultMaximum, defaultMinimum, defaultMaximum)
#     signals.append(ts2)
#     ts3 = TrafficSignal(130, defaultYellow,
#                         defaultMaximum, defaultMinimum, defaultMaximum)
#     signals.append(ts3)
#     ts4 = TrafficSignal(195, defaultYellow,
#                         defaultMaximum, defaultMinimum, defaultMaximum)
#     signals.append(ts4)


#     trustSgnl1 = TrustSignal(30.733102, 76.779132, 30.730232, 76.774572)
#     congestion.append(trustSgnl1)

#     trustSgnl2 = TrustSignal(30.732824, 76.780174 , 30.727993, 76.784416 )
#     congestion.append(trustSgnl2)

#     trustSgnl3  = TrustSignal(30.733939, 76.779321, 30.739082, 76.774892)
#     congestion.append(trustSgnl3)

#     trustSgnl4 = TrustSignal(30.733919, 76.780622, 30.740305, 76.790887)
#     congestion.append(trustSgnl4)


#     # print("congestion array -->",congestion[0].congestion_time,congestion[0].weather_description)

#     repeat()

def initialize():
    ts1 = TrafficSignal(30, 3, 0, 30, 0)  # Green: 30 sec, Yellow: 3 sec, Red: 0 sec
    signals.append(ts1)
    
    ts2 = TrafficSignal(33, 0, 0, 33, 0)   # Green: 0 sec, Yellow: 0 sec, Red: 33 sec
    signals.append(ts2)
    
    ts3 = TrafficSignal(66, 0, 0, 33, 0)   # Green: 0 sec, Yellow: 0 sec, Red: 33 sec
    signals.append(ts3)
    
    ts4 = TrafficSignal(99, 0, 0, 33, 0)   # Green: 0 sec, Yellow: 0 sec, Red: 33 sec
    signals.append(ts4)
    
    # Initialize congestion data
    trustSgnl1 = TrustSignal(30.733102, 76.779132, 30.730232, 76.774572)
    congestion.append(trustSgnl1)
    trustSgnl2 = TrustSignal(30.732824, 76.780174, 30.727993, 76.784416)
    congestion.append(trustSgnl2)
    trustSgnl3 = TrustSignal(30.733939, 76.779321, 30.739082, 76.774892)
    congestion.append(trustSgnl3)
    trustSgnl4 = TrustSignal(30.733919, 76.780622, 30.740305, 76.790887)
    congestion.append(trustSgnl4)

    repeat()


# In[13]:


# Global variables to keep track of the current direction
current_direction_index = 0
directions = ['up', 'left', 'down', 'right']

def setTime():
    # Calculate green time based on the requirement (30 seconds)
    greenTime = 30
    # Set the green time for the current signal
    signals[current_direction_index].green = greenTime
    # Set red time for the next signal
    next_signal_index = (current_direction_index + 1) % len(signals)
    signals[next_signal_index].red = defaultMaximum - greenTime

def updateValuesAfterSkip():
    buffer = signals[nextGreen].red - (defaultMinimum + defaultYellow)
    
    # Decrease the green time of the current green signal by the buffer
    signals[currentGreen].green -= buffer

    # Decrease the red time of the next green signal by the buffer
    signals[nextGreen].red -= buffer

    # Decrease the red time of the signal after the next green signal by the buffer
    signals[(nextGreen + 1) % noOfSignals].red -= buffer

    # Decrease the red time of the signal two steps ahead of the next green signal by the buffer
    signals[(nextGreen + 2) % noOfSignals].red -= buffer
    
    # Update the green time of the current green signal to be 30 seconds
    signals[currentGreen].green = defaultMinimum

    # Update the red times of the signals after the next green signal to default values
    for i in range(nextGreen, nextGreen + 3):
        signals[i % noOfSignals].red = defaultMaximum
    
    print("skipping time of direction ==>",
          directionNumbers[currentGreen])


def distanceTimeAssignment():
    global current_direction_index
    # Set the current direction based on the sequence
    current_direction = directions[current_direction_index]

    # Set green time and print the message
    setTime()
    print("Direction:", current_direction, "Green Time:", signals[current_direction_index].green)

    # Move to the next direction
    current_direction_index = (current_direction_index + 1) % len(directions)



def repeat():
    global currentGreen, currentYellow, nextGreen, current_direction_index

    # Set the green time for the current signal to 30 seconds
    signals[currentGreen].green = 30
    print("Direction:", directions[current_direction_index], "Green Time:", signals[currentGreen].green)
    
    # Update status and wait for 30 seconds
    for _ in range(30):
        printStatus()
        updateValues()
        time.sleep(1)

    # Transition to yellow signal (3-second buffer)
    signals[currentGreen].yellow = 3
    print("Direction:", directions[current_direction_index], "Yellow Time:", signals[currentGreen].yellow)
    
    # Update status and wait for 3 seconds
    for _ in range(3):
        printStatus()
        updateValues()
        time.sleep(1)

    # Reset signal times
    signals[currentGreen].green = defaultMaximum
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed

    # Move to the next direction
    current_direction_index = (current_direction_index + 1) % len(directions)
    currentGreen = current_direction_index
    nextGreen = (currentGreen + 1) % noOfSignals
    
    # Recursively repeat the process
    repeat()


def printStatus():
    for i in range(0, noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                print(" GREEN TS", i + 1, "-> r:", defaultMaximum, " y:", defaultYellow, " g:", defaultMinimum)
            else:
                print("YELLOW TS", i + 1, "-> r:", defaultMaximum, " y:", defaultYellow, " g:", defaultMinimum)
        else:
            print("   RED TS", i + 1, "-> r:", defaultMaximum, " y:", defaultYellow, " g:", defaultMinimum)
    print()

def updateValues():
    global currentGreen, currentYellow

    # Decrement the green timer of the current signal
    if not currentYellow:
        signals[currentGreen].green -= 1
        signals[currentGreen].totalGreenTime += 1

    # If the green timer of the current signal reaches 0, switch to yellow
    if signals[currentGreen].green == 0 and not currentYellow:
        currentYellow = True
        signals[currentGreen].yellow = defaultYellow

    # If the yellow timer of the current signal reaches 0, switch to the next signal
    if currentYellow and signals[currentGreen].yellow == 0:
        currentYellow = False
        currentGreen = (currentGreen + 1) % noOfSignals
        signals[currentGreen].green = defaultGreenDuration  # Set the fixed green duration

    # Decrement the red timer of all signals except the current one
    for i in range(noOfSignals):
        if i != currentGreen:
            signals[i].red -= 1




# In[17]:

def calculatetrustDynamic():
    
    global hotspot_region
    # total = 0
    # totalCrossed = 0
    # for i in range(0, noOfSignals):

    #     for j in range(0, roadLanes):

    #         total += len(vehicles[directionNumbers[i]][j])

    #     total -= vehicles[directionNumbers[i]]['crossed']
        # totalCrossed += vehicles[directionNumbers[i]]['crossed']

    # if(total != 0):
    for i in range(0, noOfSignals):
        vehicleOnOneSide = 0
        for j in range(0, roadLanes):

            for k in range(len(vehicles[directionNumbers[i]][j])):
                vehicle = vehicles[directionNumbers[i]][j][k]
                if(vehicle.crossed == 0):
                    vehicleOnOneSide += 1

        # print("Vehicle on one side = ", vehicleOnOneSide)

        # trust score defined per 100 vehicles
        x = vehicleOnOneSide
        val = math.exp(-0.03 * x)
        congestion[i].hotspot_score = round(val*weightage,2)
        # print("Pygame vehicles = ",round(val*weightage,2))
        congestion[i].trust_dynamic = round(congestion[i].congestion_score + congestion[i].weather_score + congestion[i].hotspot_score,2)
        
        # print("hotspot = ",hotspot_region)
        if hotspot_region:
            congestion[i].trust_dynamic = round(congestion[i].trust_dynamic*weightage,2)


def directionNumberFromDistribution():

    global distribution
    
    
    if len(traffic_distribution) == 0:
        distribution = [250,500,750,1000]
    else:
        distribution = traffic_distribution
    # deciding the direction_number from
    # a range of values from 1 to 1000
    
    temp = random.randint(0, 999)
    direction_number = 0
    calculatetrustDynamic()
    if(temp < distribution[0]):
        direction_number = 0
    elif(temp < distribution[1]):
        direction_number = 1
    elif(temp < distribution[2]):
        direction_number = 2
    elif(temp < distribution[3]):
        direction_number = 3

    return direction_number

def directionNumberFromtrustDynamicScores():

    calculatetrustDynamic()
    # distribution = [
    #     int(trust[0].dynamic*250), int((trust[0].dynamic+trust[1].dynamic) *
    #                            250), int((trust[0].dynamic+trust[1].dynamic+trust[2].dynamic) *
    #                                      250), int((trust[0].dynamic+trust[1].dynamic+trust[2].dynamic+trust1[3])*250)
    # ]
    trustDynamic = []
    for i in range(0,noOfSignals):
        trustDynamic.append(congestion[i].trust_dynamic)

    max_item = max(trustDynamic)
    return trustDynamic.index(max_item)



def simulationTime():

    global timeElapsed, simTime, totalWaitTime
    while(True):

        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed == simTime):
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')

            # data.append(distribution[0]/1000)
            # data.append((distribution[1] - distribution[0])/1000)
            # data.append((distribution[2] - distribution[1])/1000)
            # data.append((distribution[3] - distribution[2])/1000)

            for i in range(noOfSignals):
                print('Lane', i+1, ':',
                      vehicles[directionNumbers[i]]['crossed'])
                # data.append(vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']
            
            ###############################################################
            # totalPriorityVehiclesCrossed = 0
            
            # for i in range(noOfSignals):
            #     for j in range(roadLanes):
            #         for k in range(len(vehicles[directionNumbers[i]][j])):
            #             vehicle = vehicles[directionNumbers[i]][j][k]
            #             if(vehicle.active == True and vehicle.crossed == 1):
            #                 # print("Class = ",vehicle.vehicleClass)
            #                 # print("Wait -->",vehicle.wait_time)
            #                 totalWaitTime += vehicle.wait_time
            #                 totalPriorityVehiclesCrossed += 1

            # data.append(totalWaitTime)
            # data.append(totalPriorityVehiclesCrossed)
            # data.append(totalVehicles)
            
            # with open('../data/CaseStudy/PriorityAnalysis/4-Way-Analysis-Dynamic-Normal-Case-6.csv', 'a', newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(data)
            ###############################################################

            # data.append(totalVehicles)
            # with open('../data/4.11-Way-Analysis-Dynamic.csv', 'a', newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(data)

            # trustScoreData.append(distribution[0]/1000)
            # trustScoreData.append((distribution[1] - distribution[0])/1000)
            # trustScoreData.append((distribution[2] - distribution[1])/1000)
            # trustScoreData.append((distribution[3] - distribution[2])/1000)

            # for i in range(noOfSignals):

            #     vehicleCrossedOnOneSide = vehicles[directionNumbers[i]]['crossed']
            #     value = round(vehicleCrossedOnOneSide/totalVehicles, 2)
            #     trustScoreData.append(value)

            # with open('../data/CaseStudy/TrustScore', 'a', newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(trustScoreData)

            print('Total vehicles passed: ', totalVehicles)
            print('Total time passed: ', timeElapsed)

            os._exit(1)

def generateVehicles():
    while True:
        vehicle_type = random.randint(0, 6)
        
        # Adjust vehicle type randomly if it's a priority vehicle
        if vehicle_type == 5 or vehicle_type == 6:
            vehicle_type = random.randint(0, 4)

        # Generate random lane number
        lane_number = random.randint(0, 2)

        # Decide whether the vehicle will turn or not
        will_turn = random.randint(0, 1)

        # Generate random direction number for static traffic light
        direction_number = random.randint(0, noOfSignals - 1)

        # Create vehicle instance
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number,
                directionNumbers[direction_number], will_turn, (vehicle_type == 5 or vehicle_type == 6))

        # Sleep for a short interval before generating the next vehicle
        time.sleep(random.uniform(0.5, 1.5))


def trustScoreDataCollection():
    '''
    Initialising the csv file for trust score collection
    '''
    header = ['P1', 'P2', 'P3', 'P4', 'TrustLane1',
              'TrustLane2', 'TrustLane3', 'TrustLane4']
    # with open('./trustScore.csv', 'w', encoding='UTF8', newline='') as f:
    #     writer = csv.writer(f)
    #     # write the header
    #     writer.writerow(header)
    
    '''
    Reading possible trust scores already available
    '''
    with open('../data/CaseStudy/TrustScore/trustScore.csv', 'r') as csvfile:
        csv_dict = [row for row in csv.DictReader(csvfile)]
        if len(csv_dict) == 0:
            print('csv file is empty')
        else:
            trustScoreDict = csv_dict[-1]
            idx = 0
            for value in list(trustScoreDict.values())[4:]:
                congestion[idx].trust_static = float(value)
                idx += 1


# Checkbox class
class Checkbox:

    def __init__(self, x, y, text, font, color):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.checked = False
        self.text = font.render(text, True, color)

    def draw(self, surface):
        GRAY = (128, 128, 128)
        RED = (255, 0, 0)
        pygame.draw.rect(surface, GRAY, self.rect, 2)
        if self.checked:
            pygame.draw.rect(surface, RED, self.rect.inflate(-6, -6))
        surface.blit(self.text, (self.rect.right + 10, self.rect.centery - 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked


class Main:
    
    global hotspot_region

    thread1 = threading.Thread(
        name="simulationTime", target=simulationTime, args=())
    thread1.daemon = True
    thread1.start()

    
    thread2 = threading.Thread(
        name="initialization", target=initialize, args=())    # initialization
    thread2.daemon = True
    thread2.start()
    
    
    # thread6 = threading.Thread(
    # name="congestion", target=congestionInfo, args=())
    # thread6.daemon = True
    # thread6.start()

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)
    red = (255,0,0)
    green = (0,255,0)
    yellow = (255,255,0)

    # Screensize
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('C:\\Users\\arnav_yi3dtrt\\OneDrive\Desktop\\Ambulance Project\\Pygame Simulation\\Previous work\\images\\intersection\\intersection-4-Way.png')

    screen = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
    pygame.display.set_caption("TRAFFIC SIMULATION")

    icon = pygame.image.load('C:\\Users\\arnav_yi3dtrt\\OneDrive\Desktop\\Ambulance Project\\Pygame Simulation\\Previous work\\images\\Icons\\rush.png')
    pygame.display.set_icon(icon)

    # Loading signal images and font
    redSignal = pygame.image.load('C:\\Users\\arnav_yi3dtrt\\OneDrive\Desktop\\Ambulance Project\\Pygame Simulation\\Previous work\\images\\signals\\red.png')
    yellowSignal = pygame.image.load('C:\\Users\\arnav_yi3dtrt\\OneDrive\Desktop\\Ambulance Project\\Pygame Simulation\\Previous work\\images\\signals\\yellow.png')
    greenSignal = pygame.image.load('C:\\Users\\arnav_yi3dtrt\\OneDrive\Desktop\\Ambulance Project\\Pygame Simulation\\Previous work\\images\\signals\\green.png')
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(
        name="generateVehicles", target=generateVehicles, args=())    # Generating vehicles
    thread3.daemon = True
    thread3.start()

    # thread4 = threading.Thread(
    #     name="findPriorityVehicles", target=findActivePriorityVehicles,args=())
    # thread4.daemon = True
    # thread4.start()

    # thread5 = threading.Thread(
    # name="skipTimer", target=skipTimer, args=())
    # thread5.daemon = True
    # thread5.start()
        
    # trustScoreDataCollection()

    # thread6 = threading.Thread(
    # name="congestion", target=congestionInfo, args=())
    # thread6.daemon = True
    # thread6.start()

    # Start the listener in a new thread
    # listener_thread = threading.Thread(target=listen_for_flag_changes)
    # listener_thread.daemon = True
    # listener_thread.start()

    FPS = 60
    clock = pygame.time.Clock()
    
    # Create a checkbox
    checkbox = Checkbox(25, 25, "HOTSPOT", font, black)
    
    while True:
        
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                checkbox.handle_event(event)
                hotspot_region = checkbox.checked

        screen.blit(background, (0, 0))

        # Draw checkbox
        checkbox.draw(screen)

        # display signal and set timer according to current status: green, yellow, or red
        for i in range(0, noOfSignals):
            if(i == currentGreen):
                if(currentYellow == 1):
                    # if Emergency:
                    #     signals[i].signalText = "EMGY"
                    # else:
                    # Current signal is yellow
                    if(signals[i].yellow == 0):
                        signals[i].signalText = "STOP"
                    else:
                        signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    # if Emergency:
                    #     signals[i].signalText = "EMGY"
                    # else:
                        # Current signal is green
                    if(signals[i].green == 0):
                        signals[i].signalText = "SLOW"
                    else:
                        if displaySkip:
                            signals[i].signalText = "SKIP"
                        else:
                            signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                # if Emergency:
                #     signals[i].signalText = "EMGY"
                # else:
                    # Iterating on a red signal
                    # if(signals[i].red <= 15):
                if(signals[i].red == 0):
                    signals[i].signalText = "GO"
                else:
                    signals[i].signalText = signals[i].red
                    # else:
                    #     signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])

        signalTexts = ["", "", "", ""]
        trustDynamicTexts = ["", "", "", ""]
        trustHistoricTexts = ["", "", "", ""]
        trafficCongestionTexts = ["","","",""]
        weatherDataTexts = ["","","",""]

        for i in range(0, noOfSignals):
            signalTexts[i] = font.render(
                str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])

            displayText = vehicles[directionNumbers[i]]['crossed']

            vehicleCountTexts[i] = font.render(
                str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i], vehicleCountCoods[i])
            

            trust_color = green
            if congestion[i].trust_dynamic < weightage:
                trust_color = red
            elif congestion[i].trust_dynamic < weightage*2:
                trust_color = yellow

            trustDynamicTexts[i] = font.render(
                str("TRUST : "+str(congestion[i].trust_dynamic)), True, trust_color, black)
            screen.blit(trustDynamicTexts[i], trustHistoricCoords[i])


            # trustHistoricTexts[i] = font.render(
            #     str("H TRUST  : "+str(congestion[i].trust_static)), True, white, black)
            # screen.blit(trustHistoricTexts[i], trustHistoricCoords[i])


            trafficCongestionTexts[i] = font.render(
                str("Traffic Congestion : "+congestion[i].congestion_time),True, white, black
            )
            screen.blit(trafficCongestionTexts[i], trafficCongestionCoords[i])


            weatherDataTexts[i] = font.render(
                str("Weather : "+congestion[i].weather_description),True, white, black
            )
            screen.blit(weatherDataTexts[i], weatherDataCoords[i])



        timeElapsedText = font.render(
            ("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText, (1100, 50))

        for vehicle in simulation:

            # if((vehicle.x < 0 or vehicle.x > screenWidth) and (vehicle.y < 0 or vehicle.y > screenHeight)):
            #     vehicles[vehicle.direction][vehicle.lane].remove(vehicle)

            # else:
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()

        
        pygame.display.update()
    




# if __name__ == "main":
Main()


# In[ ]:
