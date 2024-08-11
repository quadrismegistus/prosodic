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
def web(host='127.0.0.1', port=8181, debug=False):
    """
    Start the prosodic web server.

    Args:
        host (str): The host address to bind the server to. Defaults to '127.0.0.1'.
        port (int): The port number to run the server on. Defaults to 8181.
        debug (bool): Enable debug mode if True. Defaults to False.

    Returns:
        None
    """
    from .web.app import main
    msg = f'Starting prosodic as a webserver at http://{host}:{port}...'
    click.echo(msg)
    logmap.enable()
    main(host=host, port=port, debug=debug)


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