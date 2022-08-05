import os
import math
import pickle
import hashlib
import socket as sk
from typing import List

# Some constants for the program
BUFFER=32768
PACKET=8192
SLEEP_TIME=0.001
SERVER_ADDR = ('localhost', 10000)

# Paths to the files
download_path = os.getcwd()+"/client/download/"
upload_path = os.getcwd()+"/client/upload/"
files_path = os.getcwd()+"/server/archive/"

# Socket configuration
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

# In this file, there are the functions that can be used both in the client and the server.

# This function is used to hash the list of packets to check if the file is corrupted
def hash_list(List:List)->str:
    hash = hashlib.sha256()
    for counter in List:
        hash.update(pickle.dumps(counter))
    return hash.hexdigest()

# This function is used to exchange data 
def send_data(message)->str:
    sent = sock.sendto(message.encode(), SERVER_ADDR)
    data, server = sock.recvfrom(BUFFER)
    print('%s\n\r' % data.decode('utf8'))
    return data.decode('utf8')

# This function is used to get the list of files in the archive
def get_files_list(files_path, file_name, packets_tot) -> List:
    with open(files_path + file_name, "rb") as file:
        List = []
        for i in range(packets_tot):
            toSend = {"pos": i, "value": file.read(PACKET)}
            List.append(toSend)
    return List

# This function is used to get the length of the indicated file
def get_file_length(file_name:str)->int:
    file_name= upload_path+"/"+file_name
    with open(file_name, "rb") as file:
        response = file.read()
    packets_number = 1
    size = len(response)
    if size > PACKET:
        packets_number = math.ceil(size / PACKET)
    return packets_number

# This function is used to send a help message to the client
def send_help_message(sock, address):
    help_message = 'Welcome. Please choose a command from the followings: \n\r\n- List -> get the list of the file you can download.\n\r - Get <filename> -> downloand the file from the archive. \n\r - Put <filename> -> upload the file to the archive. \n\r - Exit -> close the program.\n\r - Help -> show the available commands.\n\r'
    sock.sendto(help_message.encode(), address)

# This function is used to send a list of files to the client
def files_list(path):
    list = os.listdir(path)
    for file in list:
        if file.startswith("."):
            list.remove(file)
    return list
