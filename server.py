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

print('\n\rStarting un on %s port %s' % SERVER_ADDR)
sock.bind(SERVER_ADDR)

# Server functionalities
try:
    while True:
        print('\n\rServer is ready to receive messages.\n\r')
        data, address = sock.recvfrom(BUFFER) 
        resp = data.decode('utf8')
        if data:
            print('User connected.\n\r')
            send_help_message(sock, address)
            print('Help message sent.\n\r')
            while True:
                action, address = sock.recvfrom(BUFFER)
                response = action.decode('utf8')

                # "Exit" response implementation
                if response.lower() == 'quit':
                    print('Closing the program')
                    sock.close()
                    break

                # "List" response implementation
                elif response.lower() == 'list':
                    print('Showing files...\n\r')
                    data = 'Files stored are: ' + str(files_list(files_path))
                    sock.sendto(data.encode(), address)

                    # "Help" response implementation    
                elif response.lower() == 'help':
                    print('Sending help message...\n\r')
                    send_help_message(sock, address)

                # "Get" response implementation
                elif response[0:3].lower() == 'get':
                    file_name = response[4:]
                    try:
                        packets_tot = get_file_length(file_name)
                    except IOError:
                        print('File not found\n\r')
                        sock.sendto('404'.encode(), address)
                        continue
                    print('Sending the file to the client...\n\r')
                    sock.sendto("ACK".encode(), address)
                    sock.sendto(str(packets_tot).encode(), address)
                    List = get_files_list(files_path, file_name, packets_tot)
                    print(f"Sending packages...")
                    for packet in List:
                        sock.sendto(pickle.dumps(packet), address)
                        sleep(SLEEP_TIME)
                    sock.sendto(hash_list(List).encode(), address)
                    print('File sent.\n\r')

                # "Put" response implementation
                elif response[0:3].lower() == 'put':
                    print('Storing the file the client has sent...\n\r')
                    file_name = response[4:]
                    sock.sendto("ACK".encode(), address)
                    response, client = sock.recvfrom(BUFFER)
                    message_length = int(response.decode('utf8'))
                    packets_list=[]
                    
                    for packet in range(message_length):
                            response, client = sock.recvfrom(BUFFER)
                            response = pickle.loads(response)
                            packets_list.append(response)
                            print(f"{response['pos']}/{message_length}", end='\r')
                            packets_list.sort(key=lambda x: x['pos'])
                            data, server = sock.recvfrom(BUFFER)
                            hash = data.decode('utf8')
                            if hash != hash_list(packets_list):
                                print('ERROR: File corrupted\n\r')
                            else:
                                with open(files_path + file_name, "wb") as new_file:
                                    for packet in packets_list:
                                        new_file.write(packet['value'])
                            print(f"{file_name} file stored.")   
                
                # "Command not found" response implementation
                else:
                    send_help_message(sock, address)
        break
except Exception as error:
    print(error)
