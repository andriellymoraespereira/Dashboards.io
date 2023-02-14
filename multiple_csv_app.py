import base64
import datetime
import io

from dash import Dash, dcc, html, dash_table, Input, Output, State, MATCH, no_update
import plotly.express as px
import pandas as pd

app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1('Dashboard of Multiple Excel Sheets', style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    html.Div(id='output-data-upload', children=[]),
])

# Upload CSV and Excel sheets to the app and create the tables----------------------------------------------------------
@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('output-data-upload', 'children'),
              prevent_initial_call=True
)
def update_output(contents, filename, date, children):
    # part of the code snippet is from https://dash.plotly.com/dash-core-components/upload
    if contents is not None:
        for i, (c, n, d) in enumerate(zip(contents, filename, date)):

            content_type, content_string = contents[i].split(',')

            decoded = base64.b64decode(content_string)
            try:
                if 'csv' in filename[i]:
                    # Assume that the user uploaded a CSV file
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                elif 'xls' in filename[i]:
                    # Assume that the user uploaded an excel file
                    df = pd.read_excel(io.BytesIO(decoded))

                # Create the tables and empty graphs
                children.append(html.Div([
                    html.H5(filename[i]),

                    dash_table.DataTable(
                        df.to_dict('records'),
                        [{'name': i, 'id': i, 'selectable':True} for i in df.columns],
                        page_size=5,
                        filter_action='native',
                        column_selectable=False if filename[i]=='Toronto_temp.xlsx' else 'single',
                        selected_columns=[df.columns[4]], # preselect the 5th columns
                        style_table={'overflowX': 'auto'},
                        id={'type': 'dynamic-table',
                            'index': i},
                    ),

                    dcc.Graph(
                        id={
                            'type': 'dynamic-graph',
                            'index': i
                        },
                        figure={}
                    ),

                    # # For debugging
                    # html.Div('Raw Content'),
                    # html.Pre(contents[i][0:200] + '...', style={
                    #     'whiteSpace': 'pre-wrap',
                    #     'wordBreak': 'break-all'
                    # }),
                    html.Hr()
            ]))

            except Exception as e:
                print(e)
                return html.Div([
                    'There was an error processing this file.'
                ])
        return children
    else:
        return ""


# Build the graphs from the filtered data in the Datatable--------------------------------------------------------------
@app.callback(Output({'type': 'dynamic-graph', 'index': MATCH}, 'figure'),
              Input({'type': 'dynamic-table', 'index': MATCH}, 'derived_virtual_indices'),
              Input({'type': 'dynamic-table', 'index': MATCH}, 'selected_columns'),
              State({'type': 'dynamic-table', 'index': MATCH}, 'data')
)
def update_graph(x_axis, y_axis):

    dff = df
    # print(dff[[x_axis,y_axis]][:1])

    barchart=px.bar(
            data_frame=dff,
            x=x_axis,
            y=y_axis,
            title=y_axis+': by '+x_axis,
            # facet_col='Borough',
            # color='Borough',
            # barmode='group',
            )

    barchart.update_layout(xaxis={'categoryorder':'total ascending'},
                           title={'xanchor':'center', 'yanchor': 'top', 'y':0.9,'x':0.5,})

    return (barchart)


if __name__ == '__main__':
    app.run_server(debug=True)
