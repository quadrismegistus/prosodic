from .imports import *
import click


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command()
@click.option('--public', is_flag=True, help='enable remote connections')
@click.option('--port', default=5111, help='set port (default: 5111)')
def web(public=False, port=5111):
    from .web.app import main
    host = '0.0.0.0' if public else None
    msg = f'Starting prosodic as a webserver at http://{host}:{port}...'
    click.echo(msg)
    main(host=host, port=port)


@cli.command()
def ipython():
    click.echo('Starting prosodic in ipython')
    imps = 'from prosodic import *\nimport prosodic'
    cmd = f'ipython -i -c "{imps}"'
    os.system(cmd)
