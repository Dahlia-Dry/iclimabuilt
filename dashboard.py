from dash import Dash, callback, Output, Input, State,no_update
import dash_bootstrap_components as dbc
import pandas as pd
import datetime
from dash.exceptions import PreventUpdate
from decouple import config
import boto3
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard_components.dashboard_layout import *
import dashboard_components.email_smtp as email_smtp
import dashboard_components.settings as settings

fontawesome='https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css'
mathjax = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'

app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP,fontawesome])
app.scripts.append_script({ 'external_url' : mathjax })
server = app.server
app.layout = LAYOUT
timestream_region_name='eu-north-1'

#FETCH LATEST ICLIMABUILT DATA_____________________________________________________
s3_client = boto3.client('s3',aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                     aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
                                     region_name='eu-north-1')
#Download LivingLabs Dataset
response = s3_client.get_object(Bucket='cf606a65-feb0-4ce2-8874-3019f5724e90', Key="iclimabuilt_all.csv")
status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
if status == 200:
    lldf = pd.read_csv(response.get("Body"))
    lldf = lldf.rename(columns={'Unnamed: 0':'timestamp'})
    lldf['timestamp'] = pd.to_datetime(lldf['timestamp'])
    lldf['timestamp'] = lldf['timestamp'].dt.round('1s')
else:
    print(f"Unsuccessful S3 get_object response. Status - {status}")

#Download TEG Dataset
response = s3_client.get_object(Bucket='cf606a65-feb0-4ce2-8874-3019f5724e90', Key="teg_data.csv")
status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
if status == 200:
    tegdf = pd.read_csv(response.get("Body"))
    tegdf['timestamp'] = pd.to_datetime(tegdf['timestamp'])
    tegdf['timestamp'] = tegdf['timestamp'].dt.round('1s')
else:
    print(f"Unsuccessful S3 get_object response. Status - {status}")
#_______________________________________________________________________________
def filter_timeframe(data,startdate=None,enddate=None):
    def time_filter(row):
        if startdate is not None and row['timestamp']>=startdate:
            s_mask=True
        elif startdate is None:
            s_mask=True
        else:
            s_mask=False
        if enddate is not None and row['timestamp']<=enddate:
            e_mask=True
        elif enddate is None:
            e_mask=True
        else:
            e_mask=False
        return s_mask&e_mask
    mask = data.apply(time_filter,axis=1)
    df_filt = data[mask]
    return df_filt.sort_values(by='timestamp')

def plot_power(tegdf_t,lldf_t):
    #match up the livinglabs and TEG data to nearest timestamps using merge_asof
    cols=['timestamp','temp','rh','deltat']
    mergedf = pd.merge_asof(tegdf_t,lldf_t,on='timestamp',direction='nearest')[cols]
    mergedf['deltat'] = mergedf['deltat'].round(0)
    #calc est. output power for each timestamp
    mergedf['output power [mW]'] = [np.nan for i in range(len(mergedf))]
    for i in range(1,len(mergedf)):
        mergedf['output power [mW]'].iloc[i] = 9.7/(mergedf['timestamp'].iloc[i]-mergedf['timestamp'].iloc[i-1]).seconds
    means=mergedf.groupby('deltat',as_index=False)['output power [mW]'].mean()
    stds = mergedf.groupby('deltat',as_index=False)['output power [mW]'].std()
    counts=mergedf.groupby('deltat',as_index=False)['output power [mW]'].count()
    return go.Scatter(mode='markers',
                        x=means['deltat'],
                        y=means['output power [mW]'],
                        customdata = np.stack((np.array(stds['output power [mW]']), 
                                            np.array(counts['output power [mW]'])), axis=-1),
                        error_y=dict(
                            type='data',
                            array=stds['output power [mW]']),
                        marker=dict(color='green'),
                        name='output power',
                        hovertemplate = '<b>ΔT</b>: %{x:.2f} °C <br><b>Avg. Output Power: </b>%{y:.2f} +- %{customdata[0]:.2f} mW (n=%{customdata[1]})',)


@callback(
    [Output('delt-graph', 'figure'),
    Output('irh-graph','figure'),
    Output('isrh-graph','figure'),
    Output('power-graph','figure'),
     Output('last-updated','children')],
    [Input('data-range', 'start_date'),
     Input('data-range','end_date')]
)
def update_graphs(start_date,end_date):
    tegdf_t = filter_timeframe(tegdf,datetime.datetime.strptime(start_date,'%Y-%m-%d'),datetime.datetime.strptime(end_date,'%Y-%m-%d'))
    lldf_t = filter_timeframe(lldf,datetime.datetime.strptime(start_date,'%Y-%m-%d'),datetime.datetime.strptime(end_date,'%Y-%m-%d'))
    lldf_t['deltat'] = lldf_t['2.3.0 - 02_Outsurf']-lldf_t['2.3.1 - 02_Insurf']
    livinglab_deltat = go.Scatter(x=lldf_t['timestamp'],
                              y=lldf_t['deltat'],mode='markers',
                              marker=dict(size=3,color='lightcoral'),
                              name='LivingLab ΔT')
    livinglab_indoor_rh=go.Scatter(x=lldf_t['timestamp'],
                        y=lldf_t['2.1.1 - 02_Room_RH'],
                        hovertemplate = '%{y} %',
                        mode='markers',marker=dict(size=3,color='lightblue'),
                        name='LivingLab indoor RH')
    livinglab_insitu_rh = go.Scatter(x=lldf_t['timestamp'],
                            y=lldf_t['2.2.1 - 02_Comp_RH'],
                            mode='markers',marker=dict(size=3,color='lightblue'),
                            hovertemplate = '%{y} %',
                            name='LivingLabs in-situ RH')
    teg_t = go.Scatter(x=tegdf_t['timestamp'],
                         y=tegdf_t['temp'].astype('float'),
                         hovertemplate = '%{y:.2f} °C',
                         mode='markers',marker=dict(color='red',size=3),
                         name='TEGnology in-situ temperature')
    teg_rh = go.Scatter(x=tegdf_t['timestamp'],
                            y=tegdf_t['rh'].astype('float'),
                            hovertemplate = '%{y} %',
                            mode='markers',marker=dict(color='blue',size=3),
                            name='TEGnology in-situ RH')
    #delt_graph
    delt_fig = make_subplots(specs=[[{"secondary_y": True}]])
    delt_fig.add_trace(livinglab_deltat,secondary_y=False)
    delt_fig.add_trace(teg_t,secondary_y=False)
    delt_fig.add_trace(teg_rh,secondary_y=True)
    delt_fig.update_layout(xaxis_title='Time',hovermode='x')
    delt_fig.update_yaxes(title_text='Relative Humidity (%)',secondary_y=True,range=[0,100])
    delt_fig.update_yaxes(title_text='Temperature [°C]',secondary_y=False,range=[-30,100])
    delt_fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    #irh_graph
    irh_fig = make_subplots(specs=[[{"secondary_y": True}]])
    irh_fig.add_trace(livinglab_indoor_rh,secondary_y=False)
    irh_fig.add_trace(teg_t,secondary_y=True)
    irh_fig.add_trace(teg_rh,secondary_y=False)
    irh_fig.update_layout(xaxis_title='Time',hovermode='x')
    irh_fig.update_yaxes(title_text='Relative Humidity (%)',secondary_y=False,range=[0,100])
    irh_fig.update_yaxes(title_text='Temperature [°C]',secondary_y=True,range=[0,100] )
    irh_fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    #isrh_graph
    isrh_fig = make_subplots(specs=[[{"secondary_y": True}]])
    isrh_fig.add_trace(livinglab_insitu_rh,secondary_y=False)
    isrh_fig.add_trace(teg_t,secondary_y=True)
    isrh_fig.add_trace(teg_rh,secondary_y=False)
    isrh_fig.update_layout(xaxis_title='Time',hovermode='x')
    isrh_fig.update_yaxes(title_text='Relative Humidity (%)',secondary_y=False,range=[0,100])
    isrh_fig.update_yaxes(title_text='Temperature [C]',secondary_y=True,range=[0,100] )
    isrh_fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))
    power_fig = go.Figure()
    power_fig.add_trace(plot_power(tegdf_t,lldf_t))
    power_fig.update_layout(xaxis_title='LivingLab ΔT [°C]',
                  yaxis_title='Est. TEG Output Power [mW]',
                  title='Est. TEG Output Power vs Measured ΔT')
    last_updated=f"Last updated {str(max(tegdf_t['timestamp']))}"
    return delt_fig,irh_fig,isrh_fig,power_fig,last_updated

if __name__ == '__main__':
    app.run(debug=True)