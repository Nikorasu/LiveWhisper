#Sockets + Threads
import socket
import threading
#Model
import whisper
#Performance testing
import time
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

Model = 'tiny'      # Whisper model size (tiny, base, small, medium, large)
English = True      # Use English-only model?
Translate = False   # Translate non-English to English?

model = whisper.load_model(f'{Model}{".en" if English else ""}')

def handle_connection(connection):
    while True:
        # Wait for a response from the whisper client
        data = connection.recv(1024)
        start_time = time.time()  # record the start time
        # If there is no more data to receive, break out of the loop
        if not data:
            break

        # Send a response back to file 1
        message = model.transcribe('dictate.wav',fp16=False,language='en' if English else '',task='translate' if Translate else 'transcribe')
        end_time = time.time()  # record the end time
        execution_time = end_time - start_time  # calculate the execution time

        connection.sendall(message['text'].encode())
        logging.info(f"Whisper model execution time: {execution_time:.6f} seconds")
    # Close the connection
    connection.close()

def respond_request():
    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a public host, and a well-known port where file 1 will connect
    server_address = ('localhost', 9999)
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(5)

    while True:
        # Wait for a connection
        connection, client_address = sock.accept()

        # Create a thread to handle the connection
        connection_thread = threading.Thread(target=handle_connection, args=(connection,))
        connection_thread.start()

if __name__ == '__main__':
    respond_request()
