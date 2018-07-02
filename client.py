import time
from bluetooth import *

# Create the client socket
client_socket=BluetoothSocket( RFCOMM )

nearby_devices = {}
while len(nearby_devices) == 0:
    print "Performing inquiry..."
    nearby_devices = discover_devices(lookup_names = True)
    print "found %d devices" % len(nearby_devices)

num = 1
for name, addr in nearby_devices:
    print "%d) %s - %s" % (num, addr, name)
    num = num + 1

device = input("\nWhat device do you want to connect to? ")
(dev_mac, dev_name) = nearby_devices[device-1]

for i in range(0, 5):
    print("Attempting to connect to '%s'..." % dev_name)
    try:
        client_socket.connect((dev_mac, 1))
    except BluetoothError as err:
        print("An error occured while attempting to connect!")
        print(err)
        time.sleep(5)
        
        if i == 4:
            print("\nCould not connect to specified device, make sure you are paired and try again.")
            exit()

        continue
    break

print("\nSuccessfully connected to '%s'!" % dev_name)

print("Avaliable commands:")
print("'f' - forward")
print("'s' - stop")
print("'r' - rotate right")
print("'l' - rotate left")
print("'b' - back")
print("'exit' - terminate current session")

while True:
    cmd = raw_input("What do we want to send to the car? ")
    if cmd == "exit":
        break

    client_socket.send(cmd)
    data = client_socket.recv(1024)
    print("Reply from the car: [%s]" % data)

client_socket.close()