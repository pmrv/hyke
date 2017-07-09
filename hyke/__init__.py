from argparse import ArgumentParser
import os
import pathlib
import shutil
import subprocess
import sys
import time

description = '''
Arguments passed after '--' are given directly to simulation script, everything
else is assumed to be a argument to hyke.
'''

TIME_FMT = '%Y-%m-%d_%H-%M-%S'

class Hyke:

    def __init__(self, base = '~', verbose = False):
        '''
        base    -- the base directory to use
        verbose -- if true, print the output of the script as it runs
                   (default false)
        '''

        self.verbose = verbose
        self.base = pathlib.Path('test').expanduser().resolve()
        self.sim_base = self.base / 'sims'
        self.run_base = self.base / 'runs'

        self.by_script_base = self.run_base / 'by-script'
        self.by_script_base.mkdir(exist_ok = True)

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

    def prepare_directory(self, script):
        '''
        Prepare the run directory so that the can be run inside. In particular copy
        the script into the directory.
        '''

        shutil.copy(str(self.sim_base / script), self.run_dir)
        (self.run_dir / script).chmod(0o0444)

        by_script_link = (self.by_script_base / script)
        by_script_link.mkdir(exist_ok = True)

        (by_script_link / self.run_dir.name).symlink_to(self.run_dir)

    def execute_script(self, script, sim_args):
        '''
        Change into the run directory and execute the script.
        '''

        cli = ["python3", str(self.run_dir / script)] + list(sim_args)

        with open(self.run_dir / 'repeat', 'w') as f:
            f.write(' '.join(cli) + '\n')

        with subprocess.Popen(cli, cwd = str(self.run_dir), bufsize = 1024,
                              universal_newlines = True,
                              stdout = subprocess.PIPE) as proc, \
             open(self.run_dir / 'output', 'w') as out:
                 for l in proc.stdout:
                     out.write(l)
                     if self.verbose:
                         print(l, end = '')

def main():

    for i, a in enumerate(sys.argv):
        if a == '--': break
    else:
        i += 1

    run_args = sys.argv[1:i]
    sim_args = tuple(sys.argv[i + 1:])

    parser = ArgumentParser(description = description)
    parser.add_argument('SIM', help = 'name of the simulation script')
    parser.add_argument('-b', '--base', default = '~',
                        help = 'base directory')
    parser.add_argument('-v', '--verbose', action = 'store_true',
                        help = 'show live script output')
    args = parser.parse_args(run_args)

    hyke = Hyke(base = args.base, verbose = args.verbose)
    hyke.create_directory()
    hyke.prepare_directory(args.SIM)
    hyke.execute_script(args.SIM, sim_args)
