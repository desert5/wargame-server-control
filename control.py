#!/usr/local/bin/python3
# coding=utf-8
"""
 Wargame Server control script
 Author : DesertEagle

"""

import re
import os
from time import sleep
from subprocess import call
from enum import Enum
from random import random
from math import floor


class Rcon:
    """ Rcon connection settings """
    rconPath = "mcrcon"
    rconRemoteHost = "localhost"
    rconRemotePort = "14885"
    rconPassword = "password"

    @classmethod
    def execute(cls, command):
        """Execute rcon command, incapsulating details"""
        execution_string = cls.rconPath + ' -H ' + cls.rconRemoteHost + ' -P ' + cls.rconRemotePort + \
            ' -p ' + cls.rconPassword + ' "' + command + '"'
        call(execution_string, shell=True)


class Game:
    """Main class, containing game process manipulation"""

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

    def on_player_disconnect(self, playerid):
        pass

    def on_switch_to_game(self):
        pass

    def on_switch_to_debriefing(self):
        self.map_random_rotate()

    def on_switch_to_lobby(self):
        pass

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

    def map_random_rotate(self):
        """Rotate maps from the pool"""
        map_pool = [
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
            "Destruction_3x3_Pyeongtaek",
            "Destruction_3x3_Gangjin"
        ]

        self.currentMapId = floor(len(map_pool) * random())
        Server.change_map(map_pool[self.currentMapId])
        print("Rotating map to " + map_pool[self.currentMapId])

    def limit_level(self, playerid, playerlevel):
        """Kick players below certain level"""
        limit = 7
        if playerlevel < limit:
            print("Player level is too low: " + str(playerlevel) + ". Min is " + str(limit) + ". Kicking...")
            self.players[playerid].kick()


# ----------------------------------------------------------------------------------------------------------------------
# --------------------------------------- INTERNAL IMPLEMENTATION DETAILS ----------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

    # -------------------------------------------
    # Service event handlers
    # -------------------------------------------

    def _on_player_connect(self, match_obj):

        playerid = match_obj.group(1)
        # Creating player data structure if not present
        if not (playerid in self.players):
            self.players[playerid] = Player(playerid)

        if not self.infoRun:
            self.on_player_connect(playerid)

    # ----------------------------------------------
    def _on_player_deck_set(self, match_obj):

        playerid = match_obj.group(1)
        playerdeck = match_obj.group(2)

        self.players[playerid].set_deck(playerdeck)

        if not self.infoRun:
            self.on_player_deck_set(playerid, playerdeck)

    # ----------------------------------------------
    def _on_player_level_set(self, match_obj):

        playerid = match_obj.group(1)
        playerlevel = match_obj.group(2)

        self.players[playerid].set_level(int(playerlevel))

        if not self.infoRun:
            self.on_player_level_set(playerid, int(playerlevel))

    # ----------------------------------------------
    def _on_player_elo_set(self, match_obj):

        playerid = match_obj.group(1)
        playerelo = match_obj.group(2)

        self.players[playerid].set_elo(float(playerelo))

        if not self.infoRun:
            self.on_player_elo_set(playerid, playerelo)

    # ----------------------------------------------
    def _on_player_disconnect(self, match_obj):

        playerid = match_obj.group(1)

        if not self.infoRun:
            self.on_player_disconnect(playerid)

        del self.players[playerid]

    # ----------------------------------------------
    def _on_player_side_change(self, match_obj):

        playerid = match_obj.group(1)
        playerside = match_obj.group(2)
        self.players[playerid].set_side(Side.Redfor if playerside == '1' else Side.Bluefor)

        if not self.infoRun:
            self.on_player_side_change(playerid, playerside)

    # ----------------------------------------------
    def _on_player_name_change(self, match_obj):

        playerid = match_obj.group(1)
        playername = match_obj.group(2)
        self.players[playerid].set_name(playername)

        if not self.infoRun:
            self.on_player_name_change(playerid, playername)

    # ----------------------------------------------
    def _on_switch_to_game(self, match_obj):
        self.gameState = GameState.Game

        if not self.infoRun:
            self.on_switch_to_game()

    # ----------------------------------------------
    def _on_switch_to_debriefing(self, match_obj):
        self.gameState = GameState.Debriefing

        if not self.infoRun:
            self.on_switch_to_debriefing()

    # ----------------------------------------------
    def _on_switch_to_lobby(self, match_obj):
        self.gameState = GameState.Lobby

        if not self.infoRun:
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
    # Utility functions
    # -------------------------------------------

    def __init__(self):
        self.events = {}
        self.players = {}
        self.gameState = GameState.Lobby
        self.logfileStream = open("serverlog.txt", "r", encoding="utf-8")
        self.infoRun = True
        self.register_events()
        self.currentMapId = -1

        # Getting starting line
        while True:
            line = self.logfileStream.readline()
            if not line:
                # 0 player line is not found, reseting to the start of file
                self.logfileStream.seek(0, os.SEEK_SET)
                break

            if line == u"Variable NbPlayer set to \"0\"\n":
                # 0 player line is found, keeping this state of the stream
                break

    def __del__(self):
        self.logfileStream.close()

    def main(self):
        print("Server control script started")
        print("Gather information run")

        self.update()

        print("Gather information run is over")
        self.infoRun = False

        print("Server control started")
        while True:
            self.update()
            sleep(0.5)

    def register_event(self, regex, handler):
        """Register event handler for a certain log entry"""
        self.events[re.compile(regex)] = handler

    def update(self):
        """Parse log and trigger event handler"""
        while True:
            line = self.logfileStream.readline()
            if line:
                # Test against event expressions
                for pair in self.events.items():
                    match = pair[0].match(line)
                    if match:
                        pair[1](match)
                        break
            else:
                break

class Player:
    """
    Player data structure
    Incapsulates player data manipulation
    """

    def __init__(self, playerid):
        self._id = playerid
        self._side = Side.Bluefor
        self._deck = ""
        self._level = 0
        self._elo = 0.0
        self._name = ""

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

    def change_side(self, side):
        """Forcibly change player's side"""
        Rcon.execute("setpvar " + self._id + " PlayerAlliance " + str(side))

    def change_deck(self, deck):
        """Forcibly assign new deck to a player"""
        Rcon.execute("setpvar " + self._id + " PlayerDeckContent " + deck)

    def kick(self):
        """Kick player"""
        Rcon.execute("kick " + self._id)

    def ban(self):
        """Ban player"""
        Rcon.execute("ban " + self._id)


class Server:
    """
    Server data structure
    Incapsulates server manipulation
    """

    @classmethod
    def change_map(cls, mapname):
        Rcon.execute("setsvar Map " + mapname)

    @classmethod
    def change_name(cls, name):
        Rcon.execute("setsvar ServerName " + name)


class Side(Enum):
    Bluefor = 0
    Redfor = 1


class GameState(Enum):
    Lobby = 1
    Game = 2
    Debriefing = 3

# Starting everything
if __name__ == '__main__':
    Game().main()
