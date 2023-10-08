from dash_extensions.enrich import DashProxy, TriggerTransform, MultiplexerTransform, ServersideOutputTransform, NoOutputTransform, BlockingCallbackTransform, LogTransform, html, dcc, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import orjson

default_text="""
When in the chronicle of wasted time
I see descriptions of the fairest wights,
And beauty making beautiful old rhyme,
In praise of ladies dead and lovely knights,
Then, in the blazon of sweet beauty’s best,
Of hand, of foot, of lip, of eye, of brow,
I see their antique pen would have express’d
Even such a beauty as you master now.
So all their praises are but prophecies
Of this our time, all you prefiguring;
And for they looked but with divining eyes,
They had not skill enough your worth to sing:
For we, which now behold these present days,
Have eyes to wonder, but lack tongues to praise.
""".strip()

# Create example app.
app = DashProxy(prevent_initial_callbacks=True, external_stylesheets=[dbc.themes.COSMO])

# header
header = dbc.Container([
    logo_button := html.H1("Prosodic [prə.'sɑ.dɪk]", id='logo'),
    html.P("A metrical-phonological parser, written in Python. For English and Finnish, with flexible language support."),
    textarea := dcc.Textarea(id='inputtext', value=default_text),
    parse_button := dbc.Button('Parse', color='primary'),
    config_button := dbc.Button('Configure meter', color='secondary'),
], id='header')


app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(width=4, children=[header]),
        dbc.Col(width=8, children=[
            messagediv := dbc.Container(id="message", children=''),
            datatable := dash_table.DataTable(id='table'),
        ])
    ], id='mainrow')
], id='layout')

@app.callback(  
    Output(messagediv, 'children'),
    Input(parse_button, 'n_clicks'),
    State(textarea, 'value')
)
def echox(_, x):
    return x


if __name__ == '__main__':
    app.run(debug=True)