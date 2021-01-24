#!/usr/bin/env python

import factorio_rcon
import requests
import logging
import time
import re
import json


class Config(object):
    def __init__(self, json_conf):
        self.incoming_hook_url = json_conf.get('slack', {}).get('incoming_hook_url')
        self.poll_interval = json_conf.get('poll_interval', 30)
        self.rcon_host = json_conf['rcon']['host']
        self.rcon_port = int(json_conf['rcon']['port'])
        self.rcon_password = json_conf['rcon']['password']


class PollResult(object):
    def __init__(self, players, version):
        self.players = players
        self.version = version


player_re = re.compile("^(.+?) \\(online\\)$")


def parse_players(s):
    lines = s.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        m = player_re.match(line)
        if m:
            result.append(m.group(1))
    return result


def query_players(config):
    client = factorio_rcon.RCONClient(config.rcon_host, config.rcon_port, config.rcon_password)
    client.connect()
    try:
        response = client.send_command("/players online")
        players = parse_players(response)
        ver = client.send_command("/version")
        ver = ver.strip()
        return PollResult(players, ver)
    finally:
        client.close()


def query_players_safe(config):
    try:
        return query_players(config)
    except:
        logging.exception("Failed to query the RCON server")
        return None


def post_msg(msg, hook_url):
    r = requests.post(hook_url, json={'text': msg}, timeout=30.0)
    r.raise_for_status()
    return True


def post_msg_safe(msg, hook_url):
    try:
        return post_msg(msg, hook_url)
    except:
        logging.exception("Failed to send the message to Slack")
        return False


class ServerStatus(object):
    def __init__(self, other = None):
        if other is None:
            self.unknown = True
            self.online = False
            self.players = []
        else:
            self.unknown = other.unknown
            self.online = other.online
            self.players = other.players

    def handle_servfail(self):
        if self.unknown or self.online:
            msg = '🔴 Server is now offline.'
        else:
            msg = None
        self.online = False
        self.unknown = False
        return msg

    def handle_players(self, new_players, version):
        msg = []
        
        suppress_joins = False
        if self.unknown or not self.online:
            msg += ['🟢 Server is now online.', ('Server version: %s.' % version)]
            suppress_joins = True
        
        self.online = True
        self.unknown = False
        new_players = sorted(new_players)
        
        if new_players != self.players:
            players_joined = set(new_players) - set(self.players)
            players_left = set(self.players) - set(new_players)
            if not suppress_joins:
                if players_joined:
                    msg.append('📈 Joined: ' + ', '.join(sorted(players_joined)) + '.')
                if players_left:
                    msg.append('📉 Left: ' + ', '.join(sorted(players_left)) + '.')
            if new_players:
                msg.append('Now playing: ' + ', '.join(new_players) + '.')
            else:
                msg.append('No one is playing currently.')
        
        self.players = new_players

        if msg:
            return ' '.join(msg)
        else:
            return None


def main(config):
    status = ServerStatus()
    while True:
        new_status = ServerStatus(status)
        result = query_players_safe(config)
        if result is None:
            msg = new_status.handle_servfail()
        else:
            msg = new_status.handle_players(result.players, result.version)

        if msg is not None:
            if post_msg_safe(msg, config.incoming_hook_url):
                status = new_status
        
        time.sleep(config.poll_interval)


if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    import json
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    logging.info('Using the config file: %s', config_file)
    with open(config_file, 'rt') as conff:
        config = Config(json.loads(conff.read().strip()))
    main(config)

