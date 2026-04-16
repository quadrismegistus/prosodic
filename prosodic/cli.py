from .imports import *
import click


@click.group()
def cli():
    """
    Main command group for the CLI application.
    """
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='set host (127.0.0.1)')
@click.option('--port', default=8181, help='set port (8181)')
@click.option('--debug', is_flag=True, help='debug')
@click.option('--dev', is_flag=True, help='auto-reload backend (Python) and frontend (Svelte) on change')
def web(host='127.0.0.1', port=8181, debug=False, dev=False):
    """Start the prosodic web server."""
    from .web.api import main
    msg = f'Starting prosodic as a webserver at http://{host}:{port}...'
    click.echo(msg)
    logmap.enable()
    main(host=host, port=port, debug=debug, dev=dev)


@cli.command()
def ipython():
    """
    Start an IPython session with prosodic imported.

    This function launches an interactive IPython shell with prosodic
    pre-imported for convenience.

    Returns:
        None
    """
    click.echo('Starting prosodic in ipython')
    imps = 'from prosodic import *\nimport prosodic'
    cmd = f'ipython -i -c "{imps}"'
    os.system(cmd)