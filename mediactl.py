#!/usr/bin/env python3

# The following are basic functions for controlling available media players on a Linux system, using dbus.
# Intended for use with only one media player running, tho works with multiple just without separate controls.
# If dbus error, try setting include-system-site-packages = true in virtual environment's pyvenv.cfg file.
# by Nik Stromberg - nikorasu85@gmail.com - MIT 2022 - copilot

from dbus import SessionBus, Interface

bus = SessionBus()

def _playerlist() -> list:
    """Returns a list of all available media player services, for mediactl functions."""
    return [service for service in bus.list_names() if service.startswith('org.mpris.MediaPlayer2.')]

def playpause() -> int:
    """Toggles play/pause for all available media players, returns number successed."""
    players = _playerlist()
    worked = len(players)
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            player.PlayPause(dbus_interface='org.mpris.MediaPlayer2.Player')
        except:
            worked -= 1
    return worked

def next() -> int:
    """Go to next track for all available media players, returns number successed."""
    players = _playerlist()
    worked = len(players)
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            player.Next(dbus_interface='org.mpris.MediaPlayer2.Player')
        except:
            worked -= 1
    return worked

def prev() -> int:
    """Go to previous track for all available media players, returns number successed."""
    players = _playerlist()
    worked = len(players)
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            player.Previous(dbus_interface='org.mpris.MediaPlayer2.Player')
        except:
            worked -= 1
    return worked

def stop() -> int:
    """Stop playback for all available media players, returns number successed."""
    players = _playerlist()
    worked = len(players)
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            player.Stop(dbus_interface='org.mpris.MediaPlayer2.Player')
        except:
            worked -= 1
    return worked

def volumeup() -> int:
    """Increase volume for all available media players, returns number successed."""
    players = _playerlist()
    worked = len(players)
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            properties = Interface(player, dbus_interface='org.freedesktop.DBus.Properties')
            volume = properties.Get('org.mpris.MediaPlayer2.Player', 'Volume')
            properties.Set('org.mpris.MediaPlayer2.Player', 'Volume', volume+0.2)
        except:
            worked -= 1
    return worked

def volumedown() -> int:
    """Decrease volume for all available media players, returns number successed."""
    players = _playerlist()
    worked = len(players)
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            properties = Interface(player, dbus_interface='org.freedesktop.DBus.Properties')
            volume = properties.Get('org.mpris.MediaPlayer2.Player', 'Volume')
            properties.Set('org.mpris.MediaPlayer2.Player', 'Volume', volume-0.2)
        except:
            worked -= 1
    return worked

def status() -> list:
    """Returns list of dicts containing title, artist, & status for each media player."""
    players = _playerlist()
    details = []
    for player in players:
        try:
            player = bus.get_object(player, '/org/mpris/MediaPlayer2')
            properties = Interface(player, dbus_interface='org.freedesktop.DBus.Properties')
            metadata = properties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
            Title = metadata['xesam:title'] if 'xesam:title' in metadata else 'Unknown'
            Artist = metadata['xesam:artist'][0] if 'xesam:artist' in metadata else 'Unknown'
            PlayStatus = properties.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
            details.append({'status': str(PlayStatus), 'title': str(Title), 'artist': str(Artist)})
        except:
            pass
    return details

#if __name__ == '__main__':  # If I decide to make this a standalone media controller later.