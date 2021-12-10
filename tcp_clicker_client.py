import json
import socket
import sys
import threading
import time
import tkinter

import playsound
import pyautogui

from params import (BUF_SIZE, CLICK_KEY, CONFIG_PATH, EXIT_APP_KEY,
                    IDENTIFICATION_KEY)


def main():
    # Load config file
    connect_info = dict()
    connect_info["port"] = 0
    connect_info["ip"] = ""
    config_button: tkinter.Button = None
    with open(CONFIG_PATH, "r") as config_file:
        config_json = json.load(config_file)
        connect_info["port"] = int(config_json["port"])
        connect_info["ip"] = config_json["ip"]

    # Create small GUI
    window = tkinter.Tk("TCP Clicker Client")
    window.title("TCP Clicker Client")
    # Add entry for connection status
    client_gui_var = tkinter.StringVar()
    client_gui_var.set(f"Connecting to {connect_info['ip']}:{connect_info['port']} ...")
    tkinter.Entry(window, justify="center", textvariable=client_gui_var, width=40).pack()

    # Socket that will be created, socket is wraped in a list to be passed by reference into the thread
    sock_wrap = list()
    # Sock listen thread, is wraped in a list to be passed by reference into the thread
    sock_thread_wrap = list()

    running = True

    # Create thread to listen for clicks
    def socket_thread(sock):
        while True:
            try:
                msg = sock.recv(BUF_SIZE)
                # Wait for a click command
                if msg == CLICK_KEY:
                    print("Click")
                    pyautogui.click()
                    # Play the click sound
                    try:
                        playsound.playsound("Click.mp3", block=False)
                    except:
                        pass
                elif msg == EXIT_APP_KEY:
                    print("Server closing")
                    # Close the socket
                    sock.close()
                    # Destroy the GUI
                    client_gui_var.set(f"Connection to server closed")
                    window.after(2000, window.destroy)
                    break
            except Exception:
                if running:
                    sock.close()
                    print("Can't reach server, exiting")
                    client_gui_var.set(f"Connection to server closed")
                    window.after(2000, window.destroy)
                break

    # Connecting to server
    def connecting(sock_ref: list):
        while True:
            try:
                sock_ref.append(socket.create_connection((connect_info["ip"], connect_info["port"])))
                sock = sock_ref[0]
                # Basic identification
                sock.sendall(IDENTIFICATION_KEY)
                print(f"Connected")
                client_gui_var.set(f"Connected to {connect_info['ip']}:{connect_info['port']}")

                sock_thread = threading.Thread(target=socket_thread, args=(sock,))
                sock_thread.daemon = False
                sock_thread_wrap.append(sock_thread)
                sock_thread.start()
                print("Waiting for click...")
                window.after(0, config_button.destroy)
                break
            except Exception:
                client_gui_var.set(f"Retrying to connect to {connect_info['ip']}:{connect_info['port']} ...")
                sock_ref.clear()

    # Change IP / Port popup
    def popup_change_config():
        config_popup = tkinter.Toplevel()
        config_popup.title("Change IP / Port")
        # Label for fields
        tkinter.Label(config_popup, text="IP :").grid(column=0, row=0)
        tkinter.Label(config_popup, text="Port :").grid(column=0, row=1)
        # Entries
        config_ip = tkinter.StringVar()
        config_ip.set(f"{connect_info['ip']}")
        tkinter.Entry(config_popup, textvariable=config_ip).grid(column=1, row=0)
        config_port = tkinter.StringVar()
        config_port.set(f"{connect_info['port']}")
        tkinter.Entry(config_popup, textvariable=config_port).grid(column=1, row=1)

        def reconfig():
            # Change IP / Port
            connect_info["ip"] = config_ip.get()
            try:
                connect_info["port"] = int(config_port.get())
            except:
                # Default port
                connect_info["port"] = 25565
            if sock_thread_wrap:
                try:
                    sock_wrap[0].close()
                except Exception as e:
                    print(e)
                    pass
            # Write this in config file
            with open(CONFIG_PATH, "w") as config_file:
                json.dump(connect_info, config_file, indent=4)
            config_popup.destroy()

        # Confirm Button
        tkinter.Button(config_popup, text="OK", command=reconfig).grid(column=0, row=2, columnspan=2)

    config_button = tkinter.Button(window, text="Change IP", width=35, command=popup_change_config)
    config_button.pack()

    # Launch connection thread
    connecting_thread = threading.Thread(target=connecting, args=(sock_wrap,))
    connecting_thread.daemon = True
    connecting_thread.start()



    # Pop the GUI
    window.mainloop()

    # Used to close the sockets and exit
    print("Exiting...")
    running = False
    # Is main socket still open ?
    try:
        sock_wrap[0].sendall(EXIT_APP_KEY)
        print("Sent exit code")
        # Close main socket
        sock_wrap[0].close()
    except Exception:
        pass
    # Join Thread
    if sock_thread_wrap:
        sock_thread_wrap[0].join()
    # Exit
    sys.exit(0)
            

if __name__ == "__main__":
    main()
