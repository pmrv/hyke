import json
import pathlib
import shutil
import subprocess
import time

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
        all files from the sim_base directory into the directory and setup the
        by-* symlinks.
        '''

        for f in filter(lambda f: not f.is_dir(), self.sim_base.glob('*')):
            shutil.copy(str(f), self.run_dir, follow_symlinks = True)
            target = self.run_dir / f.name
            # remove write permissions, to guard against accidental overwriting
            target.chmod(target.lstat().st_mode & (~0o222))

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

        with open(self.run_dir / 'repeat.json', 'w') as f:
            json.dump({'executable': 'python3', 'script': script,
                       'arguments': sim_args}, f)

        with subprocess.Popen(cli, cwd = str(self.run_dir),
                              universal_newlines = True,
                              stdout = subprocess.PIPE) as proc, \
             open(self.run_dir / 'output', 'w') as out:
                 for l in proc.stdout:
                     out.write(l)
                     if self.verbose:
                         print(l, end = '')
