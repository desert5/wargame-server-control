#!/usr/local/bin/python3
# Script managing deck assignments
# coding=utf-8

import re
from time import sleep
from subprocess import call
from enum import Enum
from random import random
from math import floor

class Game:
    def __init__(self):
    
        #Variable initialization           
        self.events = {}
        self.players = {}
        self.lastProcessedLine = self.findStartingLine()    
        self.gameState = GameState.Lobby
        self.infoGatherRun = True
        
        self.rconPath = "mcrcon"
        self.rconRemoteHost = "192.168.1.13"
        self.rconRemotePort = "14885"
        self.rconPassword = "password"

        self.mapList = [
            "Destruction_2x2_port_Wonsan_Terrestre",
            "Destruction_2x3_Hwaseong",
            "Destruction_2x3_Esashi",
            "Destruction_2x3_Boseong",
            "Destruction_2x3_Tohoku",
            "Destruction_2x3_Anbyon",
            "Destruction_3x2_Boryeong_Terrestre",
            "Destruction_3x2_Taean",
            "Destruction_3x2_Taebuko",
            "Destruction_3x2_Sangju",
            "Destruction_3x2_Montagne_3",
            "Destruction_3x3_Muju",
            "Destruction_3x3_Pyeongtaek"
        ]
        self.currentMapId = -1
    
        self.registerEvents()

    # Main loop
    def start(self):
        
        print ("Server control script started")        
        
        # Gather information run
        print ("Gather information run")
        print ("Starting from line " + str(self.lastProcessedLine))
        
        self.update()
        
        # Gather information run is over
        print ("Gather information run is over")
        self.infoGatherRun = False
        
        print ("Server control started")
        while True:       

            self.update()
            
            if (self.gameState == GameState.Lobby):
                sleep(0.25)
            else:
                sleep(1)


    #-------------------------------------------
    # Event handlers
    #-------------------------------------------
    
    def onPlayerConnect (self, matchObj):
    
        playerID = matchObj.group(1)
        
        self.initPlayerData(playerID)

        
    def onPlayerDeckSet (self, matchObj):
    
        playerID = matchObj.group(1)
        playerDeck = matchObj.group(2)

        self.players[playerID]['deck'] = playerDeck
        
    def onPlayerLevelSet (self, matchObj):
    
        playerID = matchObj.group(1)
        playerLevel = matchObj.group(2)

        self.players[playerID]['level'] = int(playerLevel)
        
        if (not self.infoGatherRun):
            self.levelLimit(playerID, playerLevel)
            
        
    def onPlayerELOSet (self, matchObj):
    
        playerID = matchObj.group(1)
        playerELO = matchObj.group(2)

        self.players[playerID]['elo'] = float(playerELO)
        
    def onPlayerDisconnect (self, matchObj):
    
        playerID = matchObj.group(1)
        
        del self.players[playerID]
        
    def onPlayerChangeSide(self, matchObj):
    
        playerID = matchObj.group(1)
        playerside = matchObj.group(2)

        if (playerside == '1'):
            self.players[playerID]['side'] = Side.Redfor
        else:
            self.players[playerID]['side'] = Side.Bluefor
        
    def onSwitchToGame(self, matchObj):
    
        self.gameState = GameState.Game
        
    def onSwitchToDebriefing(self, matchObj):
    
        if (not self.infoGatherRun):
            self.mapRotate()
        
    def onSwitchToLobby(self, matchObj):
    
        self.gameState = GameState.Lobby
        

        

    
    # Register handlers for events here
    def registerEvents(self):
        self.registerEvent('Client added in session \(EugNetId : ([0-9]+)', self.onPlayerConnect)
        self.registerEvent('Client ([0-9]+) variable PlayerDeckContent set to "(.*)"', self.onPlayerDeckSet)
        self.registerEvent('Client ([0-9]+) variable PlayerLevel set to "(.*)"', self.onPlayerLevelSet)
        self.registerEvent('Client ([0-9]+) variable PlayerElo set to "(.*)"', self.onPlayerELOSet)        
        self.registerEvent('Client ([0-9]+) variable PlayerAlliance set to "([0-9])"', self.onPlayerChangeSide)
        self.registerEvent('Disconnecting client ([0-9]+)', self.onPlayerDisconnect)
        self.registerEvent('Entering in loading phase state', self.onSwitchToGame)
        self.registerEvent('Entering in debriephing phase state', self.onSwitchToGame)        
        self.registerEvent('Entering in matchmaking state', self.onSwitchToLobby)
        
    #-------------------------------------------
    # Custom actions
    #-------------------------------------------
    
    def assignDecks(self):

        generalBlueDeck = "XuAVOOkCbkxlBEyoMkgTf1Il1KtJYkaaQ9JaVnSbFS0syQUqwUlT/FVELI6A1nLhNYKTUsil9ScaLGLg"
        generalRedDeck = "tOAcF6LTLwXEYZMocldI1qnDBZdjgqZZZKW4aUMuHEbSSRMWR2SyIWytaL9KelYE/A=="

        for playerID, player in self.players.items():
            if (player['side'] == Side.Bluefor):
                if (player['deck'] != generalBlueDeck):
                    self.rconCommand("setpvar " + playerID + " PlayerDeckContent " + generalBlueDeck)

            if (player['side'] == Side.Redfor):
                if (player['deck'] != generalRedDeck):
                    self.rconCommand("setpvar " + playerID + " PlayerDeckContent " + generalRedDeck)
                    
    def mapRotate(self):
        # if (self.currentMapId == -1 or self.currentMapId == (len(self.mapList) - 1)):
            # self.currentMapId = 0
        # else:
            # self.currentMapId += 1
            
        self.currentMapId = floor(len(self.mapList)*random());
        
        print ("Rotating map to " + self.mapList[self.currentMapId])        
        self.rconCommand("setsvar Map " + self.mapList[self.currentMapId])
        
        
    def levelLimit(self, playerID, playerLevel):
        if (int(playerLevel) < 7):
            print ("Player level is too low: " + playerLevel + ". Min is 10. Kicking...")
            self.rconCommand("kick " + playerID)
    
    #-------------------------------------------
    # Utility functions
    #-------------------------------------------
    
    # Executes rcon command, incapsulating details
    def rconCommand(self, command):
        executionString = self.rconPath + ' -H ' + self.rconRemoteHost + ' -P ' + self.rconRemotePort + ' -p ' + self.rconPassword + ' "' + command + '"'
        call(executionString, shell=True)
    
    # Registers event handler for a certain log entry
    def registerEvent(self, regex, handler):
        self.events[re.compile(regex)] = handler
        
    # Init player data structure    
    def initPlayerData(self, playerID):
        if not(playerID in self.players):                    
            self.players[playerID] = {'id': playerID, 'side': Side.Bluefor, 'deck': '', 'level' : 0, 'elo' : 0.0}
    
    # Founds last time when there were 0 players on server    
    def findStartingLine(self):
        lineFound = -1
        with open("serverlog.txt", encoding='utf-8') as logfile:
            for lineNumber, line in enumerate(logfile):
                if (line == u"Variable NbPlayer set to \"0\"\n"):
                    lineFound = lineNumber
                    
        return lineFound 

    # Parses log and calls the event handler on appropriate events
    def update(self):

        with open("serverlog.txt", encoding='utf-8') as logfile:
            for line_number, line in enumerate(logfile):
                if (line_number > self.lastProcessedLine):
                    # Test against event expressions
                    for pair in self.events.items():
                        match = pair[0].match(line)
                        if (match):
                            pair[1](match)
                            break
                    self.lastProcessedLine += 1


# Sides definition
class Side(Enum):
    Bluefor = 0
    Redfor = 1    
    
class GameState(Enum):
    Lobby = 1
    Game = 2
    

# Starting everything
if __name__ == '__main__':
    Game().start()
