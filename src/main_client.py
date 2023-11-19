import zmq

context = zmq.Context()
print("Connecting to hello world server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

n = 1
for request in range(n):
    print(f"Sending request {request} ...")
    socket.send_string("Hello")
    message = socket.recv()
    print(f"Received reply {request} [ {message} ]")

if __name__ == "__main__":
    pass
