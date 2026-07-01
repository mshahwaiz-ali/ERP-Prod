# ERP-Prod

ERP-Prod contains the local Frappe installer/control scripts and custom apps used by this setup.

## What Is Included

- `install.sh` - main installer and repair launcher.
- `site_setup.sh` - site creation, site deletion, app copy/install, and site listing flow.
- `start.sh` - local development bench launcher.
- `p_apps/` - custom Frappe apps that the installer copies into the bench.

The generated Frappe bench folder is intentionally ignored by Git:

```text
frappe-bench/
```

## Install Procedure

From the project root, run:

```bash
chmod +x install.sh site_setup.sh start.sh
./install.sh
```

Then choose from the installer menu:

```text
1) Install / Setup Frappe
2) Repair Frappe
3) Start Bench
4) Site Setup
5) Exit
```

For a fresh setup, choose:

```text
1) Install / Setup Frappe
```

The installer will:

- install missing system dependencies and skip what is already installed;
- initialize `frappe-bench` with Frappe `version-15` if a valid bench does not already exist;
- keep `frappe-bench/` local only and out of Git;
- copy valid apps from `p_apps/` into the bench apps folder without overwriting existing apps;
- prepare app imports/assets;
- start bench in the background;
- open the site setup menu.

## Site Setup

You can also run site setup directly:

```bash
./site_setup.sh
```

Site setup menu:

```text
1) New Site
2) Delete Site
3) List Sites and Apps
4) Exit
```

When creating a site:

- enter a site name such as `ledgix.local` or `millitrix.local`;
- select one app, multiple apps using `1,2`, or all apps using `all`;
- the default Frappe Administrator password is `admin`;
- MariaDB database/user setup is handled automatically by the script;
- the script does not prompt for MariaDB username/password during normal site creation.

## Start Bench

To start the local development bench and print available site URLs:

```bash
./start.sh --background
```

To stop bench processes:

```bash
./start.sh --stop
```

To show status and detected sites:

```bash
./start.sh --status
```

## Logs

Installer and site setup logs are written to:

```text
install_logs/
```

Bench startup logs are written to:

```text
logs/bench-start.log
```

## Notes

- `frappe-bench/` is generated locally and should not be committed.
- Custom apps live in `p_apps/` and are committed to this repository.
- This setup is for local/development control, not a full production Nginx/Supervisor deployment.
