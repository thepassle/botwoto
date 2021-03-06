
# -*- coding: utf-8 -*-

import time
import ast
import socket
import random
import re
import urllib, json
import pymysql
import string
import requests
import datetime
import configparser
import socketserver
from threading import Thread
from datetime import datetime

# Load config.ini
config = configparser.ConfigParser()
config.read('config.ini')

class BotSocketHandler(socketserver.BaseRequestHandler):
    
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.action_dispatch = {"reload_commands": self.do_reload, "add_command": self.do_addcom, "del_command": self.do_delcom, "edit_command": self.do_editcom}
        self.data = self.request.recv(1024).strip()
        print("Incoming connection...")
        try:
            self.jsonin = json.loads(self.data.decode("UTF-8"))
        except:
            self.reply = {"result": "Error", "msg": "Invalid JSON"}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
            return
        else:  
            print("JSON: {}".format(self.jsonin))
            if "action" not in self.jsonin:
                self.reply = {"result": "Error", "msg": "Missing argument action"}
                self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                return
            try:
                self.action_dispatch[self.jsonin["action"]]()
            except:
                self.reply = {"result": "Error", "msg": "Invalid action given."}
                self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                return
        # just send back the same data, but upper-cased
    def do_reload(self):
        try:
            print("Relading commands because of remote request.")
            commands.load_commands()
        except:
            self.reply = {"result": "Error", "msg": "Loading commands failed."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
        else:
            self.reply = {"result": "OK", "msg": "Successfully reloaded commands."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))

    def do_addcom(self):
        print("Remote connection requested to add a command.")
        try:
            if all (arg in self.jsonin for arg in("level", "trigger", "response")):
                if self.jsonin["trigger"] not in commands.triggers:
                    print("Inserting new command into bot.")
                    commands.replies[self.jsonin["trigger"]] = self.jsonin["response"]
                    commands.clearances[self.jsonin["trigger"]] = self.jsonin["level"]
                    commands.triggers.append(self.jsonin["trigger"])
                else:
                    self.reply = {"result": "Error", "msg": "Command already exists."}
                    self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                    return
            else:
                self.reply = {"result": "Error", "msg": "Error missing argument for add_command."}
                self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                return
        except:
            self.reply = {"result": "Error", "msg": "Error adding new command to bot."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
        else:
            self.reply = {"result": "OK", "msg": "Successfully added command."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))

    def do_delcom(self):
        print("Remote connection requested to remove a command.")
        try:
            if "trigger" in self.jsonin:
                if self.jsonin["trigger"] in commands.triggers:
                    try:
                        print("Removing {}....".format(self.jsonin["trigger"]))
                        commands.triggers.remove(self.jsonin["trigger"])
                        commands.clearances.pop(self.jsonin["trigger"])
                        commands.replies.pop(self.jsonin["trigger"])
                    except:
                        print("Exception")
                    if (self.jsonin["trigger"] in commands.timertriggers):
                        commands.timertriggers.remove(self.jsonin["trigger"])
                        config.set("Timers", "TRIGGERS", ",".join(commands.timertriggers))
                        with open("config.ini", 'w') as configfile:
                            config.write(configfile)
                else:
                    self.reply = {"result": "Error", "msg": "Command does not exist."}
                    self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                    return
            else:
                self.reply = {"result": "Error", "msg": "Error missing argument for del_command."}
                self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                return
        except:
            self.reply = {"result": "Error", "msg": "Error removing command from bot."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
        else:
            self.reply = {"result": "OK", "msg": "Successfully removed command."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
        
    def do_editcom(self):
        print("Remote connection requested to edit a command.")
        try:
            if all (arg in self.jsonin for arg in("level", "trigger", "response")):
                if self.jsonin["trigger"] in commands.triggers:
                    print("Editing command {}.".format(self.jsonin["trigger"]))
                    commands.replies[self.jsonin["trigger"]] = self.jsonin["response"]
                    commands.clearances[self.jsonin["trigger"]] = self.jsonin["level"]
                    
                else:
                    self.reply = {"result": "Error", "msg": "Command does not exist in bot."}
                    self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                    return
            else:
                self.reply = {"result": "Error", "msg": "Error missing argument for edit_command."}
                self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
                return
        except:
            self.reply = {"result": "Error", "msg": "Error editing command in bot."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))
        else:
            self.reply = {"result": "OK", "msg": "Successfully edited command."}
            self.request.sendall(json.dumps(self.reply).encode("UTF-8"))

    
def socketloop():
   

    
    server = socketserver.TCPServer((config["Remote"]["host"], int(config["Remote"]["port"])), BotSocketHandler)
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
    server.serve_forever()

class BotCommands:

    def __init__(self):
        self.triggers = []
        self.replies = {}
        self.clearances = {}
        self.timertriggers = config["Timers"]["TRIGGERS"].split(",")
        self.timertest = False

    def load_commands(self):
        print("Loading commands...")
        self.triggers.clear()
        self.replies.clear()
        self.clearances.clear()

        allCommands = dbGetAll("SELECT * FROM commands3")


        for command in allCommands:
           
            trigger = str(command[0])
            self.triggers.append(trigger)
            reply = command[1]

        
            self.replies[trigger] = reply
            self.clearances[trigger] = str(command[2])
        

def dbGetOne(query):
    db = pymysql.connect(config["Database"]["HOSTNAME"],config["Database"]["USERNAME"],config["Database"]["PASSWORD"],config["Database"]["DBNAME"], charset='utf8mb4')
    cursor = db.cursor()
    cursor.execute(query)
    data = cursor.fetchone()
    db.close()
    return data

def dbGetAll(query):
    db = pymysql.connect(config["Database"]["HOSTNAME"],config["Database"]["USERNAME"],config["Database"]["PASSWORD"],config["Database"]["DBNAME"], charset='utf8mb4')
    cursor = db.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    db.close()
    return data

def dbExecute(query):
    
    db = pymysql.connect(config["Database"]["HOSTNAME"],config["Database"]["USERNAME"],config["Database"]["PASSWORD"],config["Database"]["DBNAME"], charset='utf8mb4')
    cursor = db.cursor()
    cursor.execute(query)
    db.close()

def dbExecuteargs(query, arg):

    db = pymysql.connect(config["Database"]["HOSTNAME"],config["Database"]["USERNAME"],config["Database"]["PASSWORD"],config["Database"]["DBNAME"], charset='utf8mb4')
    cursor = db.cursor()
    cursor.execute(query, arg)
    db.close()

def getUser(line):
    name = re.search(r'display-name=(.*?);', line)
    return name.group(1).lower()

def getMessage(line):
    # This is really not great, should fix. Works for now.
    message = re.search(r'(.*?)PRIVMSG #bradwoto :', line)
    return str(line.split(message.group(1))[1].strip().replace('PRIVMSG #bradwoto :', ''))

def openSocket():
    s = socket.socket()
    s.connect((config["Twitch"]["HOST"], int(config["Twitch"]["PORT"])))
    s.send(str("PASS " + config["Twitch"]["PASS"] + "\r\n").encode("utf-8"))
    s.send(str("NICK " + config["Twitch"]["IDENT"] + "\r\n").encode("utf-8"))
    s.send(str("JOIN #" + config["Twitch"]["CHANNEL"] + "\r\n").encode("utf-8"))
    
    return s
    
def sendMessage(s, message):
    messageTemp = "PRIVMSG #" + config["Twitch"]["CHANNEL"]+ " :" + str(message)
    s.send(str(messageTemp + "\r\n").encode("utf-8"))
    print("Sent: " + str(messageTemp.encode('utf-8')) )

def joinRoom(s):
    readbuffer = ""
    Loading = True
    while Loading:
        readbuffer = readbuffer + s.recv(1024).decode("utf-8")
        temp = str.split(readbuffer, "\n")
        readbuffer = temp.pop()
        for line in temp:
            print(line)
            Loading = loadingComplete(line)
    print("Finished Connecting...")
    s.send("CAP REQ :twitch.tv/tags\r\n".encode("UTF-8"))
    s.send("CAP REQ :twitch.tv/commands\r\n".encode("UTF-8"))
    sendMessage(s, "/mods")

def loadingComplete(line):
    if("End of /NAMES list" in line):
        return False
    else:
        return True

def is_live_stream(streamer_name):
    check_if_live = True
    while check_if_live:
        try:
            twitch_api_stream_url = "https://api.twitch.tv/kraken/streams/" + streamer_name + "?client_id=" + config["Twitch"]["CLIENT_ID"]
            streamer_html = urllib.request.urlopen(twitch_api_stream_url)
            streamer = json.loads(streamer_html.read().decode("utf-8"))

            return streamer["stream"] is not None
        except:
            print("Twitch API did not respond, trying again in 60 seconds..")
            time.sleep(60)



def taskLoop():
    is_live = False
    while True:
        if is_live or commands.timertest:
            if(len(commands.timertriggers) > 0):
                sendMessage(s, commands.replies[random.choice(commands.timertriggers)])
            time.sleep(14 * 60)
            is_live = is_live_stream(config["Twitch"]["CHANNEL"])
            if not is_live:
                sendMessage(s, "Detected channel offline.")
        else:
            if "!retweet" in commands.timertriggers:
                commands.timertriggers.remove("!retweet")
                commands.replies["!retweet"] = "Tweet for current stream not set."
                sendMessage(s, "Removed retweet timer.")
            is_live = is_live_stream(config["Twitch"]["CHANNEL"])
            if is_live:
                sendMessage(s, "Detected channel online. Starting timer..")
        time.sleep(60)


commands = BotCommands()
s = openSocket()
joinRoom(s)
readbuffer = ""
message = ""
requested=False

mods = []
permits = []


ACCESSTOKEN = config["Spotify"]["ACCESSTOKEN"]

commands.load_commands()
loopThread = Thread(target = taskLoop)
socketThread = Thread(target = socketloop)
loopThread.setDaemon(True)
socketThread.setDaemon(True)
loopThread.start()
socketThread.start()
runforever = True
while runforever:
    while runforever:
        try:

            

            try:
                chat_data =  s.recv(1024)
                if chat_data == b'':
                    raise socket.timeout
            except:
                print("Error: disconnected.. Reconnecting")
                s = openSocket()
                joinRoom(s)
                continue
            if not loopThread.is_alive():
                print("Timer thread not running..Restarting...")
                loopThread.start()
            readbuffer = readbuffer + chat_data.decode("utf-8")
            temp = readbuffer.split('\r\n')
            readbuffer = temp.pop()
            
            if readbuffer == "":
                pass
            
            for line in temp: 

                if 'subscriber=1' in line:
                    user_subscribed = True
                else: 
                    user_subscribed = False

                if "PING" in line:
                    s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                    print("Ping? Pong!")
                    continue

                if "PRIVMSG" in line:
                    user = getUser(line)
                    if user in mods:
                        print("User is moderator.")
                    message = getMessage(line)

                elif "NOTICE" in line:
                    if "moderators" in line:
                        tempmsg = line.split(":", 3)
                        tempmods = tempmsg[3].split(",")

                        mods = []
                        mods.append("karlklaxon")
                        mods.append("bradwoto")
                        for moderator in tempmods:
                            mods.append(moderator.lstrip())
                        
                        if requested:
                            sendMessage(s, "Found {} moderators.".format(len(mods)))
                            requested = False
                    continue
                else:
                    continue

                print("{} typed: {} \n".format(user, message.encode('utf-8')))
                # if re.search(r"[a-zA-Z]{2,}\.[a-zA-Z]{2,}", message) and ('clips.twitch.tv' not in message) and (user_subscribed == False or user not in mods):

                if re.search(r"[a-zA-Z]{2,}\.[a-zA-Z]{2,}", message) and ('clips.twitch.tv' not in message) and (user not in mods) and (user_subscribed == False):
                    if user.lower() in permits:
                        permits.remove(user)
                        
                    else:    
                        sendMessage(s, "/timeout "+user+" 1")
                        sendMessage(s, "@{} links are not allowed! Ask a mod for a !permit.".format(user))

#####################################################################################################################
                                                    ## COMMANDS ## 
#####################################################################################################################                


                if message[0] == "!":
                    trigger = message.strip().split(" ")[0]    

                    if trigger == "!song":
                        REFRESHTOKEN = config["Spotify"]["REFRESHTOKEN"]

                        if is_live_stream('bradWOTO'):
                            bearer = "Bearer "+str(ACCESSTOKEN)
                            r=requests.get("https://api.spotify.com/v1/me/player/currently-playing/", headers={"Authorization":str(bearer)})

                            try:
                                response = r.json()
                            except:
                                continue

                            if not str(r.text):
                                continue
                            elif 'error' in r.text:

                                headers = {"Content-Type":"application/x-www-form-urlencoded"}
                                refreshAccessToken = requests.post('https://accounts.spotify.com/api/token?grant_type=refresh_token&refresh_token='+config["Spotify"]["REFRESHTOKEN"]+'&client_id='+config["Spotify"]["CLIENTID"]+'&client_secret='+config["Spotify"]["CLIENTSECRET"], headers=headers)
                                ACCESSTOKEN = refreshAccessToken.json()['access_token']

                                time.sleep(1)

                                r=requests.get("https://api.spotify.com/v1/me/player/currently-playing/", headers={"Authorization":"Bearer "+ACCESSTOKEN})
                                response = r.json()

                            result = ''
                            if response['is_playing']:
                                for name in response['item']['artists']:
                                    result += str(name['name']) + " "

                                result += "- " + str(response['item']['name'])
                                sendMessage(s, "Brad's spotify is currently playing: " + result)
                        else:
                            print("brad is not live")

                    if trigger.lower() in commands.triggers:
                        clearance = commands.clearances[trigger.lower()]
                        reply = commands.replies[trigger.lower()]

                        if re.search(r""+trigger+" [@]?[a-zA-Z0-9]+", message ):
                            if clearance == 'mod' and user not in mods:
                                print("user not in mods")
                                pass
                            elif clearance == 'sub' and user_subscribed == False:
                                print("user not subbed")
                                pass
                            else:
                                if '@touser@' in reply or '@user@' in reply:
                                    target = message.strip().split(' ',1)[1] 
                                    print("this should replace @target in the reply and print message.")
                                    
                                    reply = reply.replace('@touser@', target)
                                    reply = reply.replace('@user@', user)
                                    sendMessage(s, reply)
                                else:
                                    target = message.strip().split(' ',1)[1] 
                                    print("this should @ target and print message.")
                                    sendMessage(s, target +": " + reply)

                        elif message == trigger:
                            if clearance == 'mod' and user not in mods:
                                print("user not in mods")
                                pass
                            elif clearance == 'sub' and user_subscribed == False:
                                print("user not subbed")
                            else:
                                print("sending")
                                reply = reply.replace('@user@', user)

                                sendMessage(s, reply)
                
                #edit command
                if (re.search(r"^!editcom ![a-zA-Z0-9]+", message )) and (user in mods):
                    print("** Editing command **")

                    updatedCommand = re.split(r'^!editcom ![a-zA-Z0-9]{2,}\b ', message)[1]
                    command = message.split(' ')[1]
                    if command.lower() not in commands.triggers:
                        sendMessage(s, "Command {} doesn't exist".format(command))
                        continue
                    else:

                        query = "UPDATE commands3 SET reply=%s WHERE command= %s"
                        dbExecuteargs(query, (updatedCommand, command))

                        updatedAt = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        query2 = "INSERT INTO history (command, reply, clearance, byUser, updatedAt) VALUES ( %s, %s, %s, %s, %s)"
                        dbExecuteargs(query2, (command, updatedCommand, clearance, user, updatedAt))

                        sendMessage(s, "Command: '"+command+"' edited.")

                        commands.load_commands()
                        continue 

                #add command
                if (re.search(r"!addcom -ul=all ![a-zA-Z0-9]+", message ) or re.search(r"!addcom -ul=mod ![a-zA-Z0-9]+", message )) and (user in mods):
                    print("** Adding command **")
                    #if theres only '!addcom' and '!someword', but no reply
                    if len(message.split(' ')) <= 3:
                        pass

                    elif len(message.split(' ')) > 3:
                        message = message.split(' ', 3)

                        clearance = str(message[1].split('=')[1])
                        command = str(message[2]).lower()
                        if command.lower() in commands.triggers:
                            sendMessage(s, "Command {} already exists".format(command))
                            continue
                        reply = str(message[3])
                        print(reply.encode("utf-8"))

                        if command[0] == '!':
                            query = "INSERT INTO commands3 (command, reply, clearance) VALUES ( %s, %s, %s)"
                            dbExecuteargs(query, (command, reply, clearance))

                            updatedAt = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            query2 = "INSERT INTO history (command, reply, clearance, byUser, updatedAt) VALUES ( %s, %s, %s, %s, %s)"
                            dbExecuteargs(query2, (command, reply, clearance, user, updatedAt))

                            sendMessage(s, "Command: '"+command+"' added.")
                            commands.triggers.append(command)
                            commands.replies[command] = reply
                            commands.clearances[command] = clearance
                            #(triggers, responses, clearances) = load_commands()
                            continue
                    
                if re.search(r"!delcom ![a-zA-Z0-9]+", message ) and (user in mods):
                    print("** Removing command **")
                    message = message.split(' ', 2)

                    dbExecute("DELETE FROM commands3 WHERE command='"+str(message[1]).strip()+"' ")
                    dbExecute("DELETE FROM history WHERE command='"+str(message[1]).strip()+"' ")

                    commands.load_commands()
                    if (message[1].lower() in commands.timertriggers):
                        commands.timertriggers.remove(message[1].lower())
                        config.set("Timers", "TRIGGERS", ",".join(commands.timertriggers))
                        with open("config.ini", 'w') as configfile:
                            config.write(configfile)
                
                        sendMessage(s, "Command {} removed from timer.".format(message[1].lower()))
                    sendMessage(s, "Command: '"+str(message[1])+"' deleted.")
                    continue
#####################################################################################################################
                                                    ## UTILS ## 
#####################################################################################################################

                if re.search(r"^!timertest$", message) and (user in mods):
                    if not commands.timertest:
                        sendMessage(s, "Manually starting timers.")
                        commands.timertest = True
                    else:
                        sendMessage(s, "Stopping timers.")
                        commands.timertest=False

                if re.search(r"^!die$", message) and (user in mods):
                    sendMessage(s, "Shutting Down...")
                    runforever = False
                    break

                if re.search(r"^!timer ![a-zA-Z0-9]+", message ) and (user in mods):
                    target = message.split(" ")[1].lower()
                    if target not in commands.triggers:
                        sendMessage(s,"Command {} does not exist".format(target))
                        continue
                    if target in commands.timertriggers:
                        commands.timertriggers.remove(target)
                        config.set("Timers", "TRIGGERS", ",".join(commands.timertriggers))
                        sendMessage(s, "Command {} removed from timer.".format(target))
                    else:
                        commands.timertriggers.append(target)
                        config.set("Timers", "TRIGGERS", ",".join(commands.timertriggers))
                        sendMessage(s, "Command {} added to timer.".format(target))
                    with open("config.ini", 'w') as configfile:
                        config.write(configfile)
                    continue
                if re.search(r"^!refreshmods", message):
                    requested = True
                    sendMessage(s, "/mods")

                if re.search(r"^!uptime", message):
                    twitch_api_stream_url = "https://api.twitch.tv/kraken/streams/bradwoto?client_id=" + config["Twitch"]["CLIENT_ID"]
                    streamer_html = urllib.request.urlopen(twitch_api_stream_url)
                    streamer = json.loads(streamer_html.read().decode("utf-8"))
                    if streamer["stream"] is None:
                        sendMessage(s, "Channel is not live.")
                        continue

                    curtime = datetime.datetime.utcnow()

                    streamstart = datetime.datetime.strptime(str(streamer["stream"]["created_at"]), '%Y-%m-%dT%H:%M:%SZ')
                    elapsed = int((curtime - streamstart) / datetime.timedelta(seconds=1))
                    hours = int(elapsed / 3600)
                    minutes = int((elapsed - (3600*hours))/60)
                    seconds = int((elapsed -((3600*hours) + (60*minutes))))
                    
                    sendMessage(s, "The stream has been live for {}:{}:{}".format(hours, str(minutes).zfill(2), str(seconds).zfill(2)))
                    


                if re.search(r"^!caster [a-zA-Z0-9_]+", message ) and (user in mods):
                    print("** Caster command **")

                    message = message.split(' ')
                    

                    twitch_api_stream_url = "https://api.twitch.tv/kraken/channels/"+message[1]+"?client_id=" + config["Twitch"]["CLIENT_ID"]
                    streamer_html = urllib.request.urlopen(twitch_api_stream_url)
                    

                    streamer = json.loads(streamer_html.read().decode("utf-8"))
                    
                    game = streamer["game"]

                    sendMessage(s, "We love @"+message[1]+", go give them a follow at www.twitch.tv/"+message[1]+" ! They were last seen playing "+str(game))
                    continue

                if re.search(r"^!permit [a-zA-Z0-9_]+", message ) and (user in mods): 
                    target = message.split(" ")[1]
                    if target not in permits:
                        permits.append(target.lower())
                        sendMessage(s, "@{}: {} has allowed you to post one link.".format(target, user))

                if re.search(r"^!tweet https://twitter.com/[a-zA-Z0-9]+/status/[0-9_]+", message ) and (user in mods):
                    url = message.split(" ")[1]
                      
                    if "!retweet" not in commands.triggers:
                        commands.triggers.append("!retweet")
                        createdtrigger = True
                    commands.replies["!retweet"] = "Let your friends know we're live and retweet out our stream: {}".format(url)
                    commands.clearances["!retweet"] = "all"
                    if "!retweet" not in commands.timertriggers:
                        commands.timertriggers.append("!retweet")
                    
                    sendMessage(s, "!retweet command and timer created/updated.")

#####################################################################################################################
                                                    ## QUOTES ## 
#####################################################################################################################

                if "!quote" in message or "!addquote" in message or "!delquote" in message:

                    if re.search(r"^!quote random$", message ):
                        print("** Quote random **")

                        

                        sent = False
                        while sent == False:
                            try:
                                
                                quotes = dbGetOne("call getrandomquote()")
                                #quote = random.choice(quotes)
                                

                                sendMessage(s, "{}".format(quotes[1]))
                                sent = True
                            except:
                                continue


                    if re.search(r"^!quote [0-9]+$", message ):
                        print("** Quote <nr> **")

                        messages = message.split(' ')
                        number = int(messages[1])
                        print(number)
                        quote = dbGetOne("SELECT * FROM quotes WHERE id = {}".format(int(number)))
                        print(quote)
                        if quote is not None:
                            sendMessage(s, "{}".format(quote[1]))
                        else:
                            sendMessage(s, "Quote #{} does not exist.".format(number))

                    if re.search(r"^!delquote [0-9]+", message ) and (user in mods):
                        print("** Remove quote **")
                        messages = message.split(' ')
                        number = int(messages[1])
                        quote = dbGetOne("SELECT * FROM quotes WHERE id = {}".format(int(number)))
                        print(quote)
                        if quote is not None:
                            dbExecute("DELETE FROM quotes WHERE id = {}".format(number))
                            sendMessage(s, "Quote #{} deleted.".format(number))
                        else:
                            sendMessage(s, "Quote #{} does not exist.".format(number))


                    if re.search(r"^!addquote", message ) and (user in mods):
                        print("** Add quote **")
                        
                        nextquote  = dbGetOne("SELECT AUTO_INCREMENT FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'quotes' AND table_schema = DATABASE( )")[0]
                        print(nextquote)
                        newquote = str(message.strip().split(' ', 1)[1])
                        date = str(datetime.datetime.now()).split(" ")[0]
                        

                        sendMessage(s, "Added quote #{}".format(nextquote))
                        dbExecuteargs('INSERT INTO quotes (quote) VALUES (%s)', ("{} {}".format(newquote, date)))


        except:
            
            print("got error, restarting")
            
            pass
        else:
            break




