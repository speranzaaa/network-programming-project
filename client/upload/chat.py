import npyscreen
import sys
import lib.server as server
import lib.client as client
from lib.form import ChatForm
from lib.form import ChatInput
import time
import curses
import socket
import datetime
import pyperclip
import os
import json
from io import StringIO

class ChatApp(npyscreen.NPSAppManaged):
    # Metodo chiamato in fase iniziale da npyscreen
    def onStart(self):

        # Tenta di trovare i settaggi nel file settings.json e carica il suo contenuto.
        # Modifica la lingua a seconda del contenuto del file settings.json
        # se il file settings.json manca, carica il file en.json
        try:
            jsonSettings = open('settings.json')
            self.settings = json.loads(jsonSettings.read())
            jsonSettings.close()
            jsonFile = open('lang/{0}.json'.format(self.settings['language']))
        except Exception:
            jsonFile = open('lang/en.json')
        self.lang = json.loads(jsonFile.read())
        jsonFile.close()

        if os.name == "nt":
            os.system("titolo P2P-Chat by Università di Bologna") # Imposta il titolo della finestra

        self.ChatForm = self.addForm('MAIN', ChatForm, name='Peer-2-Peer Chat Università di Bologna') # Aggiunge il Form della Chat come il form principale di npyscreen

        #Individua l'indirizzo IP pubblico del PC e gestisce eventuali errori
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.hostname = s.getsockname()[0]
            s.close()
        except socket.error as error:
            self.sysMsg(self.lang['nessun accesso Internet'])
            self.sysMsg(self.lang['impossibile individuare IP ADDRESS Pubblico'])
            self.hostname = "0.0.0.0"

        #Definiamo le variabili iniziali
        self.port = 3333 # la porta del server
        self.nickname = "" # variabile vuota da riempire con il nickname
        self.peer = "" # nickname del peer
        self.peerIP = "0" # IP del peer
        self.peerPort = "0" # Porta del del peer
        self.historyLog = [] # Array per raccogliere i messaggi di log
        self.messageLog = [] # Array per raccogliere i log della chat
        self.historyPos = 0 # Int per la posizione corrente nello storico dei messaggi

        

        # Inizializza i threads del Server e del Client
        self.chatServer = server.Server(self)
        self.chatServer.daemon = True
        self.chatServer.start()
        self.chatClient = client.Client(self)
        self.chatClient.start()

        # Dizionario dei comandi. Include le funzioni da chiamare e il numero degli argomenti richiesti.
        self.commandDict = {
            "connect": [self.chatClient.conn, 2],
            "disconnect": [self.restart, 0],
            "nickname": [self.setNickname, 1],
            "quit": [self.exitApp, 0],
            "port": [self.restart, 1],
            "connectback": [self.connectBack, 0],
            "clear": [self.clearChat, 0],
            "eval": [self.evalCode, -1],
            "status": [self.getStatus, 0],
            "log": [self.logChat, 0],
            "help": [self.commandHelp, 0],
            "lang": [self.changeLang, 1]
        }

        # Dizionario dei comandi alternativi
        self.commandAliasDict = {
            "nick": "nickname",
            "conn": "connect",
            "q": "quit",
            "connback": "connectback"
        }

    # Metodo per modificare la lingua dell'interfaccia. i File devono essere posizionati nella directory lang/
    def changeLang(self, args):
        self.sysMsg(self.lang['changingLang'].format(args[0]))
        try:
            jsonFile = open('lang/{0}.json'.format(args[0]))
            self.lang = json.loads(jsonFile.read())
            jsonFile.close()
        except Exception as e:
            self.sysMsg(self.lang['failedChangingLang'])
            self.sysMsg(e)
            return False
        # Save new settings
        self.settings['language'] = args[0]
        with open('settings.json', 'w') as file:
            file.write(json.dumps(self.settings))

    # Metodo per resettare i sockets del server e del client
    def restart(self, args=None):
        self.sysMsg(self.lang['restarting'])
        if not args == None and args[0] != self.port:
            self.port = int(args[0])
        if self.chatClient.isConnected:
            self.chatClient.send("\b/quit")
            time.sleep(0.2)
        self.chatClient.stop()
        self.chatServer.stop()
        self.chatClient = client.Client(self)
        self.chatClient.start()
        self.chatServer = server.Server(self)
        self.chatServer.daemon = True
        self.chatServer.start()

                
            
    # Metodo per scorrere indietro nello storico dei messaggi
    def historyBack(self, _input):
        if not self.historyLog or self.historyPos == 0:
            return False
        self.historyPos -= 1
        self.ChatForm.chatInput.value = self.historyLog[len(self.historyLog)-1-self.historyPos]

    # Metodo per scorrere avanti nello storico dei messaggi
    def historyForward(self, _input):
        if not self.historyLog:
            return False
        if self.historyPos == len(self.historyLog)-1:
            self.ChatForm.chatInput.value = ""
            return True
        self.historyPos += 1
        self.ChatForm.chatInput.value = self.historyLog[len(self.historyLog)-1-self.historyPos]

    # Metodo per impostare il nickname del client | Il Nickname è inviato al peer per identificazione
    def setNickname(self, args):
        self.nickname = args[0]
        self.sysMsg("{0}".format(self.lang['setNickname'].format(args[0])))
        if self.chatClient.isConnected:
            self.chatClient.send("\b/nick {0}".format(args[0]))

    # Metodo per visualizzare le info di sistema sul feed della chat
    def sysMsg(self, msg):
        self.messageLog.append("[SYSTEM] "+str(msg))
        if len(self.ChatForm.chatFeed.values) > self.ChatForm.y - 10:
                self.clearChat()
        if len(str(msg)) > self.ChatForm.x - 20:
            self.ChatForm.chatFeed.values.append('[SYSTEM] '+str(msg[:self.ChatForm.x-20]))
            self.ChatForm.chatFeed.values.append(str(msg[self.ChatForm.x-20:]))
        else:
            self.ChatForm.chatFeed.values.append('[SYSTEM] '+str(msg))
        self.ChatForm.chatFeed.display()

    # Metodo per inviare un messaggio ad un peer connesso
    def sendMessage(self, _input):
        msg = self.ChatForm.chatInput.value
        if msg == "":
            return False
        if len(self.ChatForm.chatFeed.values) > self.ChatForm.y - 11:
                self.clearChat()
        self.messageLog.append(self.lang['you']+" > "+msg)
        self.historyLog.append(msg)
        self.historyPos = len(self.historyLog)
        self.ChatForm.chatInput.value = ""
        self.ChatForm.chatInput.display()
        if msg.startswith('/'):
            self.commandHandler(msg)
        else:
            if self.chatClient.isConnected:
                if self.chatClient.send(msg):
                    self.ChatForm.chatFeed.values.append(self.lang['you']+" > "+msg)
                    self.ChatForm.chatFeed.display()
            else:
                self.sysMsg(self.lang['notConnected'])

    # Metodo per connettersi ad un peer che si è collegato al nostro server
    def connectBack(self):
        if self.chatServer.hasConnection and not self.chatClient.isConnected:
            if self.peerIP == "unknown" or self.peerPort == "unknown":
                self.sysMsg(self.lang['failedConnectPeerUnkown'])
                return False
            self.chatClient.conn([self.peerIP, int(self.peerPort)])
        else:
            self.sysMsg(self.lang['alreadyConnected'])

    #Metodo per registrare i log della chatin un file | I File possono essere trovati nella root directory
    def logChat(self):
        try:
            date = datetime.datetime.now().strftime("%m-%d-%Y")
            log = open("p2p-chat-log_{0}.log".format(date), "a")
            for msg in self.messageLog:
                log.write(msg+"\n")
        except Exception:
            self.sysMsg(self.lang['failedSaveLog'])
            return False
        log.close()
        self.messageLog = []
        self.sysMsg(self.lang['savedLog'].format(date))
    
   

    #Metodo per pulire il feed della chat
    def clearChat(self):
        self.ChatForm.chatFeed.values = []
        self.ChatForm.chatFeed.display()

    #Metodo per eseguire codice python nella app | Utile per visualizzare le variabili
    def evalCode(self, code):
        defaultSTDout = sys.stdout
        redirectedSTDout = sys.stdout = StringIO()
        try:
            exec(code)
        except Exception as e:
            self.sysMsg(e)
        finally:
            sys.stdout = defaultSTDout
        self.ChatForm.chatFeed.values.append('> '+redirectedSTDout.getvalue())
        self.ChatForm.chatFeed.display()
            
    # Metodo per uscire dalla app | Il comando di uscita è inviato ai peer connessi affinchè possano disconnettere i loro sockets
    def exitApp(self):
        self.sysMsg(self.lang['exitApp'])
        if self.chatClient.isConnected:
            self.chatClient.send("\b/quit")
        self.chatClient.stop()
        self.chatServer.stop()
        exit(1)

    # Metodo per incollare testo dalla clipboard nella finestra della chat
    def pasteFromClipboard(self, _input):
        self.ChatForm.chatInput.value = pyperclip.paste()
        self.ChatForm.chatInput.display()
        
    # Metodo per gestire i comandi
    def commandHandler(self, msg):
        if msg.startswith("/eval"):
            args = msg[6:]
            self.evalCode(args)
            return True

        msg = msg.split(' ')
        command = msg[0][1:]
        args = msg[1:]
        if command in self.commandAliasDict:
            command = self.commandAliasDict[command]
        if not command in self.commandDict:
            self.sysMsg(self.lang['commandNotFound'])
        else:
            if self.commandDict[command][1] == 0:
                self.commandDict[command][0]()
            elif len(args) == self.commandDict[command][1]:
                self.commandDict[command][0](args)
            else:
                self.sysMsg(self.lang['commandWrongSyntax'].format(command, self.commandDict[command][1], len(args)))

    # Metodo per visualizzare la lista dei comandi
    def commandHelp(self):
        if len(self.ChatForm.chatFeed.values) + len(self.commandDict) + 1 > self.ChatForm.y - 10:
            self.clearChat()
        self.sysMsg(self.lang['commandList'])
        for command in self.commandDict:
            if not self.lang['commands'][command] == "":
                self.sysMsg(self.lang['commands'][command])

    # Metodo per visualizzare lo stato del server e del client
    def getStatus(self):
        self.sysMsg("STATUS:")
        if self.chatServer: serverStatus = True
        else: serverStatus = False
        if self.chatClient: clientStatus = True
        else: clientStatus = False
        self.sysMsg(self.lang['serverStatusMessage'].format(serverStatus, self.port, self.chatServer.hasConnection))
        self.sysMsg(self.lang['clientStatusMessage'].format(clientStatus, self.chatClient.isConnected))
        if not self.nickname == "": self.sysMsg(self.lang['nicknameStatusMessage'].format(self.nickname))

if __name__ == '__main__':
    chatApp = ChatApp().run() # esegue la app se chat.py viene eseguito
    