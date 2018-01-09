# openproject_backup

A Python script that automates backup of OpenProject files to a remote Google Drive

It assumes the existence of [Rclone](https://rclone.org/) tool

This script can be automated to run on specified intervals using a `crontab`

## Example
Execute `crontab -e` and add the following at the end

```bash
0 1 * * * /root/backup_scripts/backup_openproject.py > /var/log/backup.log
```
