from .imports import *
import click


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command()
@click.option('--host', default='127.0.0.1', help='set host (127.0.0.1)')
@click.option('--port', default=8080, help='set port (8080)')
def web(host='127.0.0.1', port=8080):
    from .web.app import main
    msg = f'Starting prosodic as a webserver at http://{host}:{port}...'
    click.echo(msg)
    main(host=host, port=port)


@cli.command()
def ipython():
    click.echo('Starting prosodic in ipython')
    imps = 'from prosodic import *\nimport prosodic'
    cmd = f'ipython -i -c "{imps}"'
    os.system(cmd)
