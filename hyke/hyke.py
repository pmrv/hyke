import email
import json
import os
from os.path import expanduser
import pathlib
import shutil
import smtplib
import subprocess
import sys
import time

TIME_FMT = '%Y-%m-%d_%H-%M-%S'

class Hyke:

    def __init__(self, base = '~', run = 'runs', verbose = False):
        '''
        base    -- the base directory to use
        verbose -- if true, print the output of the script as it runs
                   (default false)
        '''

        self.verbose = verbose
        self.base = pathlib.Path(expanduser(base)).resolve()
        self.sim_base = self.base / 'sims'
        self.run_base = self.base / run

        self.by_script_base = self.run_base / 'by-script'
        os.makedirs(str(self.by_script_base), exist_ok = True)

        self.by_tag_base = self.run_base / 'by-tag'
        os.makedirs(str(self.by_tag_base), exist_ok = True)

    def create_directory(self):
        '''
        Create a new unique directory in RUN_BASE_DIR for the script to run in.
        '''

        run_dir = self.run_base / time.strftime(TIME_FMT)
        while run_dir.exists():
            run_dir = run_dir.with_name(run_dir.name + '~')

        run_dir.mkdir()
        self.run_dir = run_dir
        return run_dir

    def prepare_directory(self, script, tags):
        '''
        Prepare the run directory so that the can be run inside. In particular copy
        all files from the sim_base directory into the directory and setup the
        by-* symlinks.
        '''

        script = pathlib.Path(self.sim_base / script)
        script_parent = script.parent
        script_name   = script.name

        for f in filter(lambda f: not f.is_dir(),
                        script_parent.glob('*')):
            shutil.copy(str(f), str(self.run_dir), follow_symlinks = True)
            target = self.run_dir / f.name
            # remove write permissions, to guard against accidental overwriting
            target.chmod(target.lstat().st_mode & (~0o222))

        config_file = script_parent / '.hyke.json'
        if config_file.exists():
            with open(str(config_file)) as f:
                conf = json.load(f)

            try:

                for f in map(lambda f: pathlib.Path(expanduser(f)),
                             conf['linkin']):
                    if not f.is_absolute():
                        f = pathlib.Path(*['..'] * len(self.run_dir.relative_to(self.base).parts)) \
                          / f
                    (self.run_dir / f.name).symlink_to(f)

                for f in map(lambda f: pathlib.Path(expanduser(f)),
                             conf['copyin']):
                    if not f.is_absolute():
                        f = self.base / f
                    shutil.copy(str(f), str(self.run_dir), follow_symlinks = True)
            except KeyError as e:
                pass

        by_script_link = self.by_script_base / script_name
        os.makedirs(str(by_script_link), exist_ok = True)
        (by_script_link / self.run_dir.name).symlink_to(self.run_dir)

        for tag in tags:
            by_tag_link = self.by_tag_base / tag
            os.makedirs(str(by_tag_link), exist_ok = True)
            (by_tag_link / self.run_dir.name).symlink_to(self.run_dir)

    def execute_script(self, script, sim_args, send_email = None):
        '''
        Change into the run directory and execute the script.
        If email is set, a mail with the script output to the given mail.
        '''


        script = pathlib.Path(script)
        script_parent = script.parent
        script_name   = script.name

        cli = ["python3", str(self.run_dir / script_name)] + list(sim_args)

        with open(str(self.run_dir / 'repeat'), 'w') as f:
            f.write(' '.join(cli) + '\n')

        with open(str(self.run_dir / 'repeat.json'), 'w') as f:
            json.dump({'executable': 'python3', 'script': str(script),
                       'arguments': sim_args}, f)

        output_path = str(self.run_dir / 'output')
        with subprocess.Popen(cli, cwd = str(self.run_dir),
                              universal_newlines = True,
                              stdout = subprocess.PIPE) as proc, \
             open(output_path, 'w') as out:
                 for l in proc.stdout:
                     out.write(l)
                     if self.verbose:
                         print(l, end = '')

        if not send_email: return

        msg = email.message.Message()
        msg["Subject"] = ("Failed! " if proc.returncode else "Success! ") \
                       + ' '.join(cli)
        msg["From"] = "simbot"
        msg["To"] = send_email

        with open(output_path, 'rb') as of:
            msg.set_payload(of.read())

        try:
            with smtplib.SMTP("localhost") as smtp:
                smtp.send_message(msg)
        except (smtplib.SMTPException, ConnectionRefusedError):
            print("Failed to send notification email!", file = sys.stderr)
