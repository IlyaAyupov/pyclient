import configparser
import curses
import datetime
import os
import socket
import threading
from time import sleep
from zlib import compress, decompress

import ui

screen=None
from Crypto.Signature import pss
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

indent = 0

def register(name):
    global indent
    data = send(register_data(name))
    if data[:2] == b'OK':
        indent = int(data[2:].decode('utf-8'))
    return data


def register_data(name):
    keye = RSA.generate(1024)
    open("op.Key", 'wb').write(keye.publickey().export_key('PEM'))
    open("pr.Key", 'wb').write(keye.export_key('PEM'))
    ok = keye.publickey().export_key('PEM').decode('utf-8').split('\n')[1:-1]
    s = ""
    for i in ok:
        s += i
    return b'\x00' + (s + name).encode('utf-8')


def send_message(sender_id, reciever_id, group, text):
    key = RSA.import_key(open('pr.Key').read())
    h = SHA256.new(text)
    signature = pss.new(key).sign(h)
    send_data = bytearray()
    send_data.append(1)
    send_data.append(int(group))
    send_data.append(sender_id >> 16)
    send_data.append((sender_id >> 8) & 0xFF)
    send_data.append(sender_id & 0xFF)
    send_data.append(reciever_id >> 16)
    send_data.append((reciever_id >> 8) & 0xFF)
    send_data.append(reciever_id & 0xFF)
    send_data += signature + text
    return send_data


def send(data):
    sock = socket.socket()
    sock.connect(('167.172.32.117', 1337))
    data = compress(data)
    ou = bytearray()
    ou.append(len(data) >> 8)
    ou.append(len(data) & 0xFF)
    ou += data
    sock.send(ou)
    leng = sock.recv(2)
    leng = (leng[0] << 8) + leng[1]
    return decompress(sock.recv(leng))


def get_users():
    return b'\x02'


def get_messages():
    out = bytearray()
    out.append(3)
    out.append(indent >> 16)
    out.append((indent >> 8) & 0xFF)
    out.append((indent) & 0xFF)
    return out

def _start_curses():
    global screen
    screen = curses.initscr()
    curses.cbreak()
    screen.keypad(1)

def redraw():
    screen.refresh()
    history.redraw()
    title.redraw()
    prompt.redraw()
def updater():
    while True:
        messes = send(get_messages()).decode('utf-8')
        if messes.count(':') > 0:
            messes = messes.split('\n')

            for i in messes:
                recid = i[:i.index(':')]
                text = i[i.index(':') + 1:]
                try:
                    usr = users_dict[int(recid)]
                except KeyError:
                    usr = "UNK"
                msg = ui.Message(datetime.datetime.now(), usr, text)

                history.append(msg)
        history.redraw()
        sleep(3)
_start_curses()
layout = ui.Layout()
title   = ui.Title(layout, screen)
history = ui.History(layout, screen)
prompt  = ui.Prompt(layout, screen)

redraw()

if not (os.path.exists("config.cfg") and os.path.exists("op.Key") and os.path.exists("pr.Key")):
    history.append(ui.Message(datetime.datetime.now(),"Введи имя",""))
    history.redraw()
    nam = prompt.getstr().decode('utf-8')
    history.messages=[]
    history.redraw()
    config = configparser.ConfigParser()
    config.add_section("Chat")
    config.set("Chat", "username", nam)
    register(nam)
    config.set("Chat", "id", str(indent))
    with open("config.cfg", "w") as config_file:
        config.write(config_file)

if (os.path.exists("config.cfg") and os.path.exists("op.Key") and os.path.exists("pr.Key")):
    config = configparser.ConfigParser()
    config.read("config.cfg")
    name = config["Chat"]["username"]
    indent = int(config["Chat"]["id"])





    history.messages=[]
    users = send(get_users()).decode('utf-8').strip()
    users_dict = {}
    for i in users.split('\n'):
        users_dict.update({int(i.strip().split(':')[0]): i.strip().split(':')[1]})
    for i in users_dict:
        history.append(ui.Message(datetime.datetime.now(),"ВЫБИРАЙ",f"{i}: {users_dict[i]}"))
        history.redraw()
    try:
        to=int(prompt.getstr().decode('utf-8'))
    except Exception:
        to = int(prompt.getstr().decode('utf-8'))
    history.messages=[]
    history.redraw()
    t = threading.Thread(target=updater)
    t.start()
while True:
        redraw()
        text = prompt.getstr()
        if text == b'':
            continue
        if text == b'/quit':
            break
        send(send_message(indent, to, False, text))
        now = datetime.datetime.now()
        msg = ui.Message(now, "ME", text)
        history.append(msg)

        history.redraw()
        prompt.reset()

