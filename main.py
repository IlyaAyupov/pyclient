import configparser
import os
import socket
from zlib import compress, decompress

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


if not (os.path.exists("config.cfg") and os.path.exists("op.Key") and os.path.exists("pr.Key")):
    print("Enter your name:")
    nam = input()
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
    while True:
        print("Chose:\n\t1-write message\n\t2-give messages")
        choise = int(input())
        if choise == 1:
            print(f"Chose reciever:\n{send(get_users()).decode('utf-8')}")
            rec_id = int(input())
            print("Enter text:")
            text = input()
            if send(send_message(indent, rec_id, False, text.encode('utf-8'))) != b'ERROR':
                print("Suck")
                continue
        if choise == 2:
            print(send(get_messages()).decode('utf-8'))
