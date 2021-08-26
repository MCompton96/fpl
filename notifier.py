from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from setting import *
import smtplib, ssl

with open('data/transfers.json', 'r') as f:
    transfer_info = json.load(f)

with open('data/my_team_info.json', 'r') as f:
    team_info = json.load(f)

bank = transfer_info['bank'] / 10
budget = team_info['last_deadline_value'] / 10

events = pd.read_csv('./data/events.csv')

def get_cron_date(date):

    day = date.day
    month = date.month
    hour = date.hour
    minute = date.minute
    cron = f'{minute} {hour} {day} {month} *'

    return cron

def get_gameweek():
    gw = 0
    for id in events.index:
        if events["is_current"][id] == True:
            gw = events["id"][id] 

    return gw

def get_deadline():

    now = datetime.utcnow()
    for i in events.index:
        deadline_date = datetime.strptime(events['deadline_time'][i], '%Y-%m-%dT%H:%M:%SZ')
        if deadline_date > now:
            break

    deadline_date = deadline_date + timedelta(hours=1)
    deadline_date = deadline_date.strftime('%d %b, %Y %H:%M')
    return deadline_date


def html_response(transfers):
    '''
    Creates a HTML response to be sent through email.
    '''

    style = '''
        <style>
            body {
                font-family: arial, sans-serif;
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            .header {
                background: #37003c88;
                color: #ffffff;
            }
            td, th {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            tr:nth-child(even) {
                background: #eeeeee;
            }
            .btn {
                font-family: Arial, sans-serif;
                background: #37003c;
                border: none;
                color: #ffffff;
                padding: 8px 16px;
                text-decoration: none;
                display: inline-block;
                cursor: pointer;
                border-radius: 4px;
            }
        </style>
    '''

    html = ''
    for transfer in transfers:
        html += f'''
            <tr>
                <td>{transfer['out']['name'].title()}<small>[£{transfer['out']['cost']}]</small></td>
                <td>{transfer['in']['name'].title()}<small>[£{transfer['in']['cost']}]</small></td>
                <td>{transfer['points']}</td>
                <td>{transfer['g/l']}</td>
            </tr>
        '''
    
    response = f'''
        <!DOCTYPE html>
        <html>
        <head>
            {style}
        </head>
        <body>
            <h3>Potential Transfers</h3>
            <table>
                <tr>
                    <th>Out</th>
                    <th>In</th>
                    <th>Points</th>
                    <th>Gain/Loss</th>
                </tr>
                {html}
            </table>
            <br>
            <h3>Important Stats</h3>
            <p>Next <b>deadline</b> is <b>{get_deadline()}</b></p>
            <p>Your <b>team value</b> is <b>£{budget}m</b></p>
            <p>You have <b>£{bank}m</b> in your <b>bank</b></p>
            <br>
        </body>
        </html>
    '''

    return response

def send_email(content):

    sender_email = EMAIL_SETTINGS["Sender"]
    receiver_email =EMAIL_SETTINGS["Receiver"]
    password = EMAIL_SETTINGS["password"]

    message = MIMEMultipart('alternative')
    message['Subject'] = f'Fantasy AI - Gameweek {get_gameweek()}'
    message['From'] = sender_email
    message['To'] = receiver_email

    part = MIMEText(content, 'html')
    message.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    


