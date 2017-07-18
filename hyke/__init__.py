from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import sys

from .hyke import Hyke

description = '''
Arguments passed after '--' are given directly to simulation script, everything
else is assumed to be a argument to hyke.
'''

def main():

    for i, a in enumerate(sys.argv):
        if a == '--': break
    else:
        i += 1

    run_args = sys.argv[1:i]
    sim_args = tuple(sys.argv[i + 1:])

    parser = ArgumentParser(description = description,
                            formatter_class = ArgumentDefaultsHelpFormatter)
    parser.add_argument('SIM', help = 'name of the simulation script')
    parser.add_argument('-b', '--base', default = '~',
                        help = 'base directory')
    parser.add_argument('-p', '--prepare-only', action = 'store_true',
                        help = 'only prepare the run directory without '
                               'executing the script, print the run diractory')
    parser.add_argument('-r', '--run', default = 'runs',
                        help = 'directory where runs should be stored.')
    parser.add_argument('-t', '--tags', nargs = '*',
                        help = 'tags describing the run')
    parser.add_argument('-e', '--email', default = None,
                        help = 'send script output to this mail on completion')
    parser.add_argument('-v', '--verbose', action = 'store_true',
                        help = 'show live script output')
    args = parser.parse_args(run_args)

    hyke = Hyke(base = args.base, run = args.run, verbose = args.verbose)
    run_dir = hyke.create_directory()
    hyke.prepare_directory(args.SIM, args.tags)
    if args.prepare_only:
        print(run_dir)
    else:
        hyke.execute_script(args.SIM, sim_args, email = args.email)
