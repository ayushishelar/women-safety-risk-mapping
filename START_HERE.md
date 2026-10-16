# Start here — one step at a time

This guide is for the first time you are running the project on your Windows computer. You do **not** need to understand the ML code yet.

## Step 1: get the project folder

Download and extract `women-safety-risk-mapping-starter.zip` somewhere easy to find, such as your Documents folder. Open the extracted folder. You should see `README.md`, `requirements.txt`, and an `ml` folder.

## Step 2: open a terminal in that folder

In File Explorer, open the extracted project folder. Click the address bar at the top, type `powershell`, and press Enter. A PowerShell window should open in the project folder.

Type this command and press Enter:

```powershell
py --version
```

You should see a version, for example `Python 3.12.6`. If you see an error, copy the exact message and ask for help before continuing.

## Step 3: create a private Python workspace for this project

Only after Step 2 works, type these commands one at a time:

```powershell
py -3 -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

The prompt should now begin with `(.venv)`. This is a local environment for this project; it keeps its Python packages separate from other projects.

If PowerShell says scripts are disabled, stop and copy that message. There is a safe alternative; do not change computer-wide security settings.

## Step 4: install the project packages

```powershell
python -m pip install -r requirements.txt
```

Wait for it to finish. If you see an error, copy the last 10–15 lines.

## Step 5: train the demonstration model

```powershell
python ml\train.py
```

This creates an invented dataset, trains a small model, prints an evaluation, and saves a model file on your computer. The invented data is for learning only; it cannot assess real-world safety.

## Step 6: try one example

```powershell
python ml\predict.py
```

For now, your only goal is to get the command working. The longer `README.md` explains how the pieces fit together and how Git will help you save and share changes with teammates.
