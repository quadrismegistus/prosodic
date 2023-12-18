from .imports import *
import click


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command()  # @cli, not @click!
def web():
    click.echo('Starting prosodic as a webserver...')
    from .web.app import main
    main()


@cli.command()  # @cli, not @click!
def ipython():
    click.echo('Starting prosodic in ipython')
    imps = 'from prosodic import *\nimport prosodic'
    cmd = f'ipython -i -c "{imps}"'
    os.system(cmd)
