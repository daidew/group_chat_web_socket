#Client Side
import socket
import select
import sys
import time
import os
import subprocess as sp
# sp.call('cls',shell=True)
# os.system('clear')
cls = lambda: print('\n' * 100)
cls()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 50006))
data = None
con, con2 = False, False
while True:
    st, st2 = '', ''
    for i in range(10):
        r_s, w_s, x_s = select.select([s, sys.stdin], [], [], 0.01)
        for sock in r_s:
            if sock == s:
                data = s.recv(1024)
                if not data:
                    print('\n**** Disconnected from server ****\n')
                    sys.exit()
                else:
                    st2 += data.decode()
                    con2 = True
            else:
                con = True
                st += sys.stdin.readline().strip()

    if con:
        con = False
        s.sendall(st.encode('utf-8'))
        # cls()
        os.system('clear')
    if con2:
        con2 = False
        os.system('clear')
        print(st2, end='')
        sys.stdout.flush()
    
        
