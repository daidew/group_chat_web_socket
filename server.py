#Server side
import socket
import time
from datetime import datetime
import select
import threading

class ChatSystem():

    def __init__(self):
        self.room_index = dict()
        self.current_room_index = -1
        self.username_db = {}

    def RegisterUser(self, addr):
        #addr = (ip, port)
        self.username_db[addr] = 'anon'

    def Username(self, addr):
        try:
            return self.username_db[addr]
        except:
            return b'anon (lookup failed)'

    def CreateChatRoom(self, x):
        try:
            x = int(x)
            if x in self.room_index:
                print('room {} has already created'.format(x))
                return -99
            else:
                self.room_index[x] = ChatRoom(x)
                print('Create chat room successful')
                return 0
        except Exception as e:
            print('Create chat room failed ({})'.format(e))
            return -1

    def JoinChatRoom(self, x):
        try:
            x = int(x)
            if x in self.room_index:
                self.current_room_index = x
                return 0
            else:
                print('Room {} does not exist. You need to create first'.format(x))
                return -99
        except:
            print('Join chat room failed')
            return -1

    def DeleteChatRoom(self, x):
        try:
            x = int(x)
            if x in self.room_index:
                del self.room_index[x]
                return 0
            else:
                print('Room {} does not exist.'.format(x))
                return -99
        except:
            print('Delete chat room failed')
            return -1

    def ListAllChatRoom(self):
        a = list(self.room_index.keys())
        st = ''
        if len(a) == 0:
            st = "There are no created rooms yet"
        else:
            st = 'Active Room(s): ' + ','.join(str(x) for x in a)
        st = st + '\n'
        st = st.encode('utf-8')
        return st
    
    def UpdateUsername(self, addr, username):
        _ = self.Username(addr)
        self.username_db[addr] = username.decode()
        print('changed username from {} to {}'.format(_, self.Username(addr)))
        return 0

    def GetCurrentChatRoom(self):
        try:
            return self.room_index[self.current_room_index]
        except Exception as e:
            print('error fetching current chat room ({})'.format(e))
            return -1

class ChatRoom():

    def __init__(self, room_id=0, message_cnt_limit=10):
        self.room_id = room_id
        self.message_list = []
        self.MESSAGE_CNT_LIMIT = message_cnt_limit
    def Render(self):
        st = "------------ Room {} ------------\n".format(self.room_id).encode('utf-8')
        for message in self.message_list[-self.MESSAGE_CNT_LIMIT:]:
            st += message.RenderMessage()

        return st

    def ProcessQuery(self, username, st):
        try:
            st = st.decode()
            if st == '\exit':
                return 2
            else:
                message = self.AddMessage(username, st)
                return 0
        except Exception as e:
            print('Process query failed ({})'.format(e))
            return -1

    def AddMessage(self, username, message):
        chatMessage = ChatMessage(username, message)
        self.message_list.append(chatMessage)
        return chatMessage


class ChatMessage():
    
    def __init__(self, username, message):
        self.timestamp = datetime.now()
        self.message = message
        self.username = username

    def RenderMessage(self):
        return ('['+self.timestamp.strftime("%H:%M:%S")+'] '+self.username+': '+self.message+'\n').encode('utf-8')


chatSystem = ChatSystem()

def server(conn, addr):
    WELCOME_MESSAGE = \
b"=========== Welcome! ==============\n\
Enter following number to:\n\
    (1) Create Chat room\n\
    (2) Join chat room\n\
    (3) List available chat room\n\
    (4) Set username\n\
    (5) Exit program\n\
\
Who needs password anyway?\n\
===================================\n"
    state = 0
    inp = -1
    data = None
    print('Initiate Server')
    print('Connected by', addr)

    chatSystem.RegisterUser(addr)

    while True:
        if state == 0:
            print('state 0')
            conn.sendall(WELCOME_MESSAGE)
            conn.sendall("{}> ".format(chatSystem.Username(addr)).encode('utf-8'))
            data = conn.recv(1024)
            print('Recieved:',data)

            try:
                inp = int(data.decode())
            except:
                print('error decoding data input')
                conn.sendall(b"You have entered illegal/incorrect input. Please try again!\n")
                inp = -1
                state = 0
                continue

            if inp == 1:
                #create chat room
                print('creating chat room')
                conn.sendall(b"Enter room name you wish to create: ")
                room_num = conn.recv(1024)
                print('Recieved:',room_num)
                res = chatSystem.CreateChatRoom(room_num)
                if res == 0:
                    conn.sendall("Create room {} successful\n".format(room_num.decode()).encode('utf-8'))
                    state = 0 #back to menu
                else:
                    conn.sendall("Create room {} failed. Error code {}\n".format(room_num.decode(), res).encode('utf-8'))
                    state = 0
            elif inp == 2:
                #join chat room
                print('joining chat room')
                conn.sendall(b"Please enter room number: ")
                room_num = conn.recv(1024)
                print('Recieved:',room_num)
                res = chatSystem.JoinChatRoom(room_num)
                if res == 0:
                    conn.sendall("Join room {} successful\n(type `\exit` to quit)\n".format(room_num.decode()).encode('utf-8'))
                    state = 1
                else:
                    conn.sendall("Join room {} failed. Error code {}\n".format(room_num.decode(), res).encode('utf-8'))
                    state = 0

            elif inp == 3:
                #list chat room
                print('listing chat room')
                roomNameList = chatSystem.ListAllChatRoom()
                conn.sendall(roomNameList)
                state = 0

            elif inp == 4:
                #update username
                print('updating username')
                conn.sendall(b"Please enter your new username: ")
                username = conn.recv(1024)
                print('Recieved:',username)
                res = chatSystem.UpdateUsername(addr, username)
                if res == 0:
                    conn.sendall(b"Update username successful\n")
                    state = 0
                else:
                    conn.sendall(b"Update username failed. Error code {}\n".format(res).encode('utf-8'))
                    state = 0
            elif inp == 5:
                print('exiting program')
                return 0
            else:
                print('invalid inp',inp)
                conn.sendall(b"You have entered illegal/incorrect input. Please try again!\n")
                inp = -1
                state = 0
        elif state == 1:
            #in the chat room
            print('state 1')
            chatRoom = chatSystem.GetCurrentChatRoom()
            conn.settimeout(3)
            while True:
                data = chatRoom.Render()
                conn.sendall(data)
                conn.sendall("{}> ".format(chatSystem.Username(addr)).encode('utf-8'))
                try:
                    data = conn.recv(1024)
                except:
                    continue
                res = chatRoom.ProcessQuery(chatSystem.Username(addr), data)
                if type(res) == int:
                    if res == 2:
                        #exit chat room
                        print('Exiting chat room {}'.format(chatRoom.room_id))
                        state = 0
                        break
                    elif res == 1:
                        print('chat error')
                        state = 0
                        break

            conn.settimeout(None)

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 50006))
    s.listen(5)
    server_list = []
    # conn, addr = s.accept()
    # server_list.append(server(conn, addr))
    for i in range(5):
        threading.Thread(target=server, args=(s.accept())).start()

