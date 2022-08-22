######################################
# Angela Speranza                      
# angela.speranza@studio.unibo.it
# Matricola: 0000992169
######################################

import pickle
import socket as sk
from time import sleep
from typing import List
from common_functionalities import *

# Socket configuration
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

message = '\n\rConnecting to server...'
print(message)

# Client functionalities
try:
    sent = sock.sendto(message.encode(), SERVER_ADDR)
    data, server = sock.recvfrom(BUFFER)
    print('%s\n\r' % data.decode('utf8'))

    while True:
        print('Write a command:')
        message = input()

        # "Exit" command implementation
        if message.lower() == 'exit':
                print('Closing the program...')
                sent = sock.sendto(message.encode(), SERVER_ADDR)
                sock.close()
                break

        # "List" command implementation
        elif message.lower() == 'list':
            print('\n\rShowing files...')
            send_data(message.lower())

        # "Help" command implementation
        elif message.lower() == 'help':
            print('\n\rShowing help...')
            send_data(message.lower())

        # "Get" command implementation
        elif message[0:3].lower() == 'get':
            print('\n\rDownloading file...')
            sent = sock.sendto(message.encode(), SERVER_ADDR)
            data, server = sock.recvfrom(BUFFER)
            if  data.decode('utf8') == '404':
                    print('ERROR: File not found\n\r')
            else:
                    print('%s\n\r' % data.decode('utf8'))
                    data, server = sock.recvfrom(BUFFER)
                    message_length = int(data.decode('utf8'))
                    packets_list=[]
                    for packet in range(message_length):
                        data, server = sock.recvfrom(BUFFER)
                        data = pickle.loads(data)
                        packets_list.append(data)
                        print(f"{data['pos']}/{message_length}", end='\r')
                    packets_list.sort(key=lambda x: x['pos'])
                    data, server = sock.recvfrom(BUFFER)
                    hash = data.decode('utf8')
                    if hash != hash_list(packets_list):
                        print('ERROR: File corrupted\n\r')
                    else:
                        with open(download_path + message[4:], "wb") as downloaded_file:
                            for packet in packets_list:
                               downloaded_file.write(packet['value'])
                        print(f"Downloaded {message[4:]} file from server")
                
        # "Put" command implementation
        elif message[0:3].lower() == 'put':
            file_name = message[4:]
            try:
                packets_tot = get_file_length(file_name)
            except IOError:
                    print('File not found\n\r')
                    continue
            print('\n\rUploading file...')
            sent = sock.sendto(message.encode(), SERVER_ADDR)
            data, server = sock.recvfrom(BUFFER)
            print('%s\n\r' % data.decode('utf8'))
            packets_tot = get_file_length(file_name)
            sock.sendto(str(packets_tot).encode(), SERVER_ADDR)
            List = get_files_list(upload_path, file_name, packets_tot)
            print(f"Sending packages...")
            for packet in List:
                sock.sendto(pickle.dumps(packet), SERVER_ADDR)
                sleep(SLEEP_TIME)
            sock.sendto(hash_list(List).encode(), SERVER_ADDR)
            print('File sent!!\n\r')

        # Command not found
        else:
            print('\n\rInvalid command')

except Exception as info:
        print(info)
