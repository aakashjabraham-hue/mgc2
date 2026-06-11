# C2 Server Web Panel

A Flask-based C2 panel to establish a remote connection with machines. I have added the listener script as well. 
This uses a "mailbox" system by sending messages to a dynamically generated malibox linked to your machine id, in order to distinguish mailboxes. You send the commands, the machine reads them, and sends back the output through the command shell


## Project Structure
* `/static/` - Contains CSS and visual assets.
* `/templates/` - Contains HTML layout files.

## Environment Variables
Before running the application, ensure the following environment variables are configured:

| Variable | Description |
| :--- | :--- |
| `DASHBOARD_USER` | The admin username required to log into the panel. |
| `DASHBOARD_PASS` | The admin password required to log into the panel. |
| `FLASK_SECRET_KEY` | Secret key used to securely encrypt session data. |
| `DATABASE_URL` | The connection string for your hosted SQL database (e.g., PostgreSQL). |

## Local Testing
To run and test the application locally, set up your environment variables and execute:
```bash
python app.py
