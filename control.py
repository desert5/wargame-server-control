#!/usr/local/bin/python3
# coding=utf-8
# --------------------------------------------------
# Wargame server control script
# Author : DesertEagle
# --------------------------------------------------

import re
from time import sleep
from subprocess import call
from enum import Enum
from random import random
from math import floor

class Rcon:
    def __init__(self):
        self.rconPath = "mcrcon"
        self.rconRemoteHost = "localhost"
        self.rconRemotePort = "14885"
        self.rconPassword = "password"

    # Executes rcon command, incapsulating details
    def exec(self, command):
        execution_string = self.rconPath + ' -H ' + self.rconRemoteHost + ' -P ' + self.rconRemotePort + \
            ' -p ' + self.rconPassword + ' "' + command + '"'
        call(execution_string, shell=True)


class Game:
    def __init__(self):

        # -------------------------------------------
        # Initialization
        # -------------------------------------------

        self.events = {}
        self.players = {}
        self.lastProcessedLine = self.find_starting_line
        self.gameState = GameState.Lobby
        self.rcon = Rcon()
        self.info_run = True

        self.map_pool = [
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

        self.register_events()

    # Main loop
    def start(self):

        print("Server control script started")

        # Gather information run
        print("Gather information run")
        print("Starting from line " + str(self.lastProcessedLine))

        self.update()

        # Gather information run is over
        print("Gather information run is over")
        self.info_run = False

        print("Server control started")
        while True:
            self.update()
            sleep(0.5)

    # -------------------------------------------
    # User event handlers
    # -------------------------------------------

    def on_player_connect(self, playerid):
        pass

    def on_player_deck_set(self, playerid, playerdeck):
        pass

    def on_player_level_set(self, playerid, playerlevel):
        self.limit_level(playerid, playerlevel)

    def on_player_elo_set(self, playerid, playerelo):
        pass

    def on_player_side_change(self, playerid, playerside):
        pass

    def on_player_name_change(self, playerid, playername):
        pass

    def on_switch_to_game(self):
        pass

    def on_switch_to_debriefing(self):
        self.map_random_rotate()

    def on_switch_to_lobby(self):
        pass

    # -------------------------------------------
    # Service event handlers
    # -------------------------------------------

    def _on_player_connect(self, match_obj):

        playerid = match_obj.group(1)
        # Creating player data structure if not present
        if not (playerid in self.players):
            self.players[playerid] = Player(playerid)

        if not self.info_run:
            self.on_player_connect(playerid)

    # ----------------------------------------------
    def _on_player_deck_set(self, match_obj):

        playerid = match_obj.group(1)
        playerdeck = match_obj.group(2)

        self.players[playerid].set_deck(playerdeck)

        if not self.info_run:
            self.on_player_deck_set(playerid, playerdeck)

    # ----------------------------------------------
    def _on_player_level_set(self, match_obj):

        playerid = match_obj.group(1)
        playerlevel = match_obj.group(2)

        self.players[playerid].set_level(int(playerlevel))

        if not self.info_run:
            self.on_player_level_set(playerid, playerlevel)

    # ----------------------------------------------
    def _on_player_elo_set(self, match_obj):

        playerid = match_obj.group(1)
        playerelo = match_obj.group(2)

        self.players[playerid].set_elo(float(playerelo))

        if not self.info_run:
            self.on_player_elo_set(playerid, playerelo)

    # ----------------------------------------------
    def _on_player_disconnect(self, match_obj):

        playerid = match_obj.group(1)

        del self.players[playerid]

    # ----------------------------------------------
    def _on_player_side_change(self, match_obj):

        playerid = match_obj.group(1)
        playerside = match_obj.group(2)
        self.players[playerid].set_side(Side.Redfor if playerside == '1' else Side.Bluefor)

        if not self.info_run:
            self.on_player_side_change(playerid, playerside)

    # ----------------------------------------------
    def _on_player_name_change(self, match_obj):

        playerid = match_obj.group(1)
        playername = match_obj.group(2)
        self.players[playerid].set_name(playername)

    # ----------------------------------------------
    def _on_switch_to_game(self, matchObj):
        self.gameState = GameState.Game

        if not self.info_run:
            self.on_switch_to_game()

    # ----------------------------------------------
    def _on_switch_to_debriefing(self, matchObj):
        self.gameState = GameState.Debriefing

        if not self.info_run:
            self.on_switch_to_debriefing()

    # ----------------------------------------------
    def _on_switch_to_lobby(self, matchObj):
        self.gameState = GameState.Lobby

        if not self.info_run:
            self.on_switch_to_lobby()

    # ---------------------------------------------
    # Event handlers registration
    # ---------------------------------------------

    def register_events(self):
        self.register_event('Client added in session \(EugNetId : ([0-9]+)', self._on_player_connect)
        self.register_event('Client ([0-9]+) variable PlayerDeckContent set to "(.*)"', self._on_player_deck_set)
        self.register_event('Client ([0-9]+) variable PlayerLevel set to "(.*)"', self._on_player_level_set)
        self.register_event('Client ([0-9]+) variable PlayerElo set to "(.*)"', self._on_player_elo_set)
        self.register_event('Client ([0-9]+) variable PlayerAlliance set to "([0-9])"', self._on_player_side_change)
        self.register_event('Client ([0-9]+) variable PlayerName set to "(.*)"', self._on_player_name_change)
        self.register_event('Disconnecting client ([0-9]+)', self._on_player_disconnect)
        self.register_event('Entering in loading phase state', self._on_switch_to_game)
        self.register_event('Entering in debriephing phase state', self._on_switch_to_debriefing)
        self.register_event('Entering in matchmaking state', self._on_switch_to_lobby)

    # -------------------------------------------
    # Custom actions
    # -------------------------------------------

    # Forcing certain deck usage
    def assign_decks(self):

        general_blue_deck = "XuAVOOkCbkxlBEyoMkgTf1Il1KtJYkaaQ9JaVnSbFS0syQUqwUlT/FVELI6A1nLhNYKTUsil9ScaLGLg"
        general_red_deck = "tOAcF6LTLwXEYZMocldI1qnDBZdjgqZZZKW4aUMuHEbSSRMWR2SyIWytaL9KelYE/A=="

        for playerID, player in self.players.items():
            if player.get_side() == Side.Bluefor:
                if player.get_deck() != general_blue_deck:
                    player.change_deck(general_blue_deck)

            if player.get_side() == Side.Redfor:
                if player.get_deck() != general_red_deck:
                    player.change_deck(general_red_deck)

    # Rotates maps from the pool
    def map_random_rotate(self):
        self.currentMapId = floor(len(self.map_pool) * random())

        print("Rotating map to " + self.map_pool[self.currentMapId])
        self.rcon.exec("setsvar Map " + self.map_pool[self.currentMapId])

    # Kicks players below certain level
    def limit_level(self, playerid, playerlevel):
        if int(playerlevel) < 7:
            print("Player level is too low: " + playerlevel + ". Min is 7. Kicking...")
            self.players[playerid].kick()

    # -------------------------------------------
    # Utility functions
    # -------------------------------------------

    # Registers event handler for a certain log entry
    def register_event(self, regex, handler):
        self.events[re.compile(regex)] = handler

    # Founds last time when there were 0 players on server    
    @property
    def find_starting_line(self):
        linefound = -1
        with open("serverlog.txt", encoding='utf-8') as logfile:
            for lineNumber, line in enumerate(logfile):
                if line == u"Variable NbPlayer set to \"0\"\n":
                    linefound = lineNumber

        return linefound

    # Parses log and calls the event handler on appropriate events
    def update(self):

        with open("serverlog.txt", encoding='utf-8') as logfile:
            for line_number, line in enumerate(logfile):
                if line_number > self.lastProcessedLine:
                    # Test against event expressions
                    for pair in self.events.items():
                        match = pair[0].match(line)
                        if match:
                            pair[1](match)
                            break
                    self.lastProcessedLine += 1


# ------------------------------------
# Player data structure
# Incapsulate player data manipulation
# ------------------------------------

class Player:
    def __init__(self, playerid):
        self._id = playerid
        self._side = Side.Bluefor
        self._deck = ""
        self._level = 0
        self._elo = 0.0
        self._name = ""

        self.rcon = Rcon()

    # Getters
    def get_id(self):
        return self._id

    def get_side(self):
        return self._side

    def get_deck(self):
        return self._deck

    def get_level(self):
        return self._level

    def get_elo(self):
        return self._elo

    def get_name(self):
        return self._name

    # Setters
    def set_side(self, side):
        self._side = side

    def set_deck(self, deck):
        self._deck = deck

    def set_level(self, level):
        self._level = level

    def set_elo(self, elo):
        self._elo = elo

    def set_name(self, name):
        self._name = name

    # ------------------------------
    # Manipulation logic for the player
    # ------------------------------

    # ------------------------------------------
    # Function to change player`s side
    # side: side you want to assign to a player
    # ------------------------------------------
    def change_side(self, side):
        self.rcon.exec("setpvar " + self._id + " PlayerAlliance " + str(side))

    # ------------------------------------------
    # Function to change player`s deck
    # deck: deck you want to assign to a player
    # ------------------------------------------
    def change_deck(self, deck):
        self.rcon.exec("setpvar " + self._id + " PlayerDeckContent " + deck)

    def kick(self):
        self.rcon.exec("kick " + self._id)

    def ban(self):
        self.rcon.exec("ban " + self._id)


# Sides definition
class Side(Enum):
    Bluefor = 0
    Redfor = 1


class GameState(Enum):
    Lobby = 1
    Game = 2
    Debriefing = 3

# Starting everything
if __name__ == '__main__':
    Game().start()
