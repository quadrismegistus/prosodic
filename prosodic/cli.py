from .imports import *
import click


@click.group()
def cli():
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='set host (127.0.0.1)')
@click.option('--port', default=8181, help='set port (8181)')
@click.option('--debug', is_flag=True, help='debug')
def web(host='127.0.0.1', port=8181, debug=False):
    from .web.app import main
    msg = f'Starting prosodic as a webserver at http://{host}:{port}...'
    click.echo(msg)
    logmap.enable()
    main(host=host, port=port, debug=debug)


@cli.command()
def ipython():
    click.echo('Starting prosodic in ipython')
    imps = 'from prosodic import *\nimport prosodic'
    cmd = f'ipython -i -c "{imps}"'
    os.system(cmd)
