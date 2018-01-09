#!/usr/bin/env python3

import subprocess
import smtplib
import tarfile
import string
import sys
import os


OP_BACKUP_CMD = 'sudo openproject run backup'
OP_BACKUP_DIR = '/var/db/openproject/backup'
GD_REMOTE = 'remote:Backups/openproject'
ARCHIVE_PREFIX = 'op_backup'

exit_code = 0
error_msg = ''

MAIL_USER = 'XXXXXX'
MAIL_PWD = 'XXXXXX'
MAIL_FROM = 'OpenProject Backup Service'
MAIL_TO = 'XXXXXX'
MAIL_SUBJECT = 'OpenProject Backup Failed'


def assert_tools():
    global exit_code
    # Check pre-requisites

    # Assert that Rclone is installed
    exists = is_tool('rclone')
    if not exists:
        error_msg = 'Rclone is not installed'
        print(error_msg)
        send_email(MAIL_SUBJECT, error_msg)
        exit_code = 1
        return exit_code


def backup(argv=None):
    global exit_code
    p1 = subprocess.Popen(OP_BACKUP_CMD, stdout=subprocess.PIPE, shell=True)
    p2 = subprocess.Popen(["grep", OP_BACKUP_DIR],
                          stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    files = p2.communicate()[0].decode('utf-8').splitlines()

    timestamp = get_timestamp(files[0])
    # Compress files to a single archive
    tmp_archive = '/tmp/' + ARCHIVE_PREFIX + '-' + timestamp + '.tar'

    print('Archiving all backup files to', tmp_archive)
    tar = tarfile.open(tmp_archive, "w")
    for f in files:
        tar.add(f, os.path.basename(f))
    tar.close()

    exit_code = upload_to_gdrive(tmp_archive)
    if (exit_code != 0):
        send_email(MAIL_SUBJECT, error_msg)

    # Last steo - if no error was caught, then do cleanup
    if (exit_code == 0):
        # Do cleanup here
        print('Cleaning Up temporary archive')
        os.remove(tmp_archive)

        print('Cleaning up OpenProject backups')
        for f in files:
            os.remove(f)

    return exit_code

# The timestamp is located between the 2nd occurence of '-' and the first occurence of '.'


def get_timestamp(filename):
    try:
        start = filename.rindex('-') + len('-')
        end = filename.index('.', start)
        return filename[start:end]
    except ValueError:
        return ""


def upload_to_gdrive(archive):
    global exit_code
    global error_msg
    print('Copying ' + archive + ' to remote ' + GD_REMOTE)
    returncode = subprocess.call(
        'rclone mkdir remote:' + GD_REMOTE, shell=True)

    if (returncode != 0):
        error_msg = 'Could not create remote Google Drive directory'
        print(error_msg)
        return returncode

    returncode = subprocess.call(
        'rclone copy ' + archive + ' ' + GD_REMOTE, shell=True)

    if (returncode != 0):
        error_msg = 'Could not copy archive to remote Google Drive directory'
        print(error_msg)
        return returncode

    return returncode


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    # from whichcraft import which
    from shutil import which

    return which(name) is not None


def send_email(subject, body):
    TO = MAIL_TO if type(MAIL_TO) is list else [MAIL_TO]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (MAIL_FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(MAIL_USER, MAIL_PWD)
        server.sendmail(MAIL_FROM, TO, message)
        server.close()
        print('successfully sent the mail')
    except:
        print('failed to send mail')


if __name__ == "__main__":
    assert_tools()

    if (exit_code != 1):
        backup()

    sys.exit(exit_code)
