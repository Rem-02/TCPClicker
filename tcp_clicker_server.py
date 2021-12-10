import json
import select
import socket
import sys
import threading
import tkinter

import keyboard
import playsound
import pyautogui

from params import (BUF_SIZE, CLICK_KEY, CONFIG_PATH, EXIT_APP_KEY,
                    IDENTIFICATION_KEY)


def main():
    # Load config file
    port = 0
    with open(CONFIG_PATH, "r") as config_file:
        config_json = json.load(config_file)
        port = int(config_json["port"])
    with socket.create_server(('', port)) as sock:
        # Clients list to click
        clients_list = list()
        
        # Fonction to send click action to client
        def send_click():
            list_to_remove = list()
            client: socket.socket
            for client in clients_list:
                try:
                    # Send the click key to all clients
                    send_thread = threading.Thread(target=client["sock"].sendall, args=(CLICK_KEY,))
                    send_thread.daemon = True
                    send_thread.start()
                except Exception:
                    # Can't send, remove it
                    list_to_remove.append(client)
            # Also click here too
            pyautogui.click()
            # Play the click sound
            try:
                playsound.playsound("Click.mp3", block=False)
            except:
                pass
            # Clean the list
            for client in list_to_remove:
                clients_list.remove(client)
                print("A client has been removed")
            # Update GUI
            nb_clients = len(clients_list)
            print(f"Clicked for {nb_clients} client{'s' if nb_clients > 1 else ''}")
            clients_gui_var.set(f"{nb_clients} client{'s' if nb_clients > 1 else ''}")

        # Register k key to send click
        keyboard.add_hotkey("ctrl+alt+c", send_click, suppress=True)

        # Create small GUI
        window = tkinter.Tk("TCP Clicker Serveur")
        window.title("TCP Clicker Serveur")
        # Add entry for number of clients
        clients_gui_var = tkinter.StringVar()
        clients_gui_var.set("0 client")
        tkinter.Entry(justify="center", textvariable=clients_gui_var, width=30).pack()

        running = True

        # Listen for exit code of the clients
        def client_listen_thread(client):
            while True:
                try:
                    msg = client["sock"].recv(BUF_SIZE)
                    if msg == EXIT_APP_KEY:
                        # Remove this client from the list
                        clients_list.remove(client)
                        print(f"{client['address']} disconnected")
                        # Update GUI
                        nb_clients = len(clients_list)
                        clients_gui_var.set(f"{nb_clients} client{'s' if nb_clients > 1 else ''}")
                        window.after(0, client["button"].destroy)
                        break
                except Exception:
                    # Something went wrong, exiting
                    # Check if is the list
                    if client in clients_list:
                        print("Client listen error")
                        clients_list.remove(client)
                        print(f"{client['address']} disconnected")
                        # Update GUI
                        nb_clients = len(clients_list)
                        clients_gui_var.set(f"{nb_clients} client{'s' if nb_clients > 1 else ''}")
                        window.after(0, client["button"].destroy)
                    break

        # Kick the client
        def kick_client(client):
            print(f"Kicking {client['address']}")
            # Remove it from the list
            try:
                clients_list.remove(client)
            except Exception:
                print("Client not in list")
                pass
            # Update GUI
            nb_clients = len(clients_list)
            clients_gui_var.set(f"{nb_clients} client{'s' if nb_clients > 1 else ''}")
            window.after(0, client["button"].destroy)
            try:
                # Send close
                client["sock"].sendall(EXIT_APP_KEY)
                client["sock"].close()
                client["thread"].join()
            except Exception:
                pass

        # Create thread to listen for clients
        def socket_thread():
            # Listen for a connection
            sock.listen(5)
            while running:
                # Got a client
                client = dict()
                try:
                    client["sock"], client["address"] = sock.accept()
                except Exception:
                    continue
                print(f"{client['address']} connected")
                # Wait for it to send the key or timeout after 5 seconds
                client["sock"].settimeout(5.0)
                try:
                    if IDENTIFICATION_KEY == client["sock"].recv(BUF_SIZE):
                        print("Client identified")
                        # Add it to the list
                        clients_list.append(client)
                        # Remove timeout
                        client["sock"].settimeout(None)
                        # Update GUI
                        nb_clients = len(clients_list)
                        clients_gui_var.set(f"{nb_clients} client{'s' if nb_clients > 1 else ''}")
                        # Add a button for this client
                        client["button"] = tkinter.Button(window, text=f"{client['address']}", width=25)
                        client["button"]["command"] = lambda client=client: kick_client(client)
                        window.after(0, client["button"].pack)
                        # Listen to it
                        client_thread = threading.Thread(target=client_listen_thread, args=(client,))
                        client_thread.daemon = True
                        client["thread"] = client_thread
                        client_thread.start()
                    else:
                        print("Client dropped")
                        client["sock"].close()
                except Exception:
                    print("Client dropped")
                    client["sock"].close()
        sock_thread = threading.Thread(target=socket_thread)
        sock_thread.start()
        print("Waiting for clients...")
        print("CTRL + ALT + C to Click")

        # Pop the GUI
        window.mainloop()

        # Used to close the sockets and exit
        print("Exiting...")
        running = False
        # Close main socket
        sock.close()
        # Join Thread
        sock_thread.join()
        # Close clients
        for client in clients_list:
            try:
                # Send the close key to all clients
                client["sock"].sendall(EXIT_APP_KEY)
                client["sock"].close()
                client["thread"].join()
            except Exception:
                pass
        # Exit
        sys.exit(0)

if __name__ == "__main__":
    main()
