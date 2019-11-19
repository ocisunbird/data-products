"""
Generate district level scans, plays and unique devices on a weekly basis
"""
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from azure.common import AzureMissingResourceHttpError
from utils import create_json, get_data_from_blob, post_data_to_blob


# TODO: Remove DIKSHA specific filters from query
def district_devices(result_loc_, date_, query_, state_):
    """
    compute unique devices for a state over a week
    :param result_loc_: pathlib.Path object to store resultant CSV at.
    :param date_: datetime object to use for query and path
    :param query_: json template for query
    :param state_: state to be used in query
    :return: None
    """
    slug_ = result_loc_.name
    start_date = date_ - timedelta(days=7)
    with open(file_path.parent.joinpath('resources').joinpath(query_)) as f:
        query = f.read()
    query = query.replace('state_name', state_)
    query = query.replace('start_date', datetime.strftime(start_date, '%Y-%m-%dT00:00:00+00:00'))
    query = query.replace('end_date', datetime.strftime(date_, '%Y-%m-%dT00:00:00+00:00'))
    response = requests.request("POST", url, data=query, headers=headers)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return
        data = []
        for response in response.json():
            data.append(response['event'])
        df = pd.DataFrame(data).fillna('Unknown')
        df.to_csv(result_loc_.parent.joinpath("{}_district_devices.csv".format(slug_)), index=False)
        post_data_to_blob(result_loc_.parent.joinpath("{}_district_devices.csv".format(slug_)), backup=True)
        df['Unique Devices'] = df['Unique Devices'].astype(int)
        df = df.join(city_district[city_district['state'] == state_].set_index('City'), on='City', how='left').fillna(
            'Unknown').groupby(['District', 'Platform'])['Unique Devices'].sum().reset_index()
        df.to_csv(result_loc_.parent.joinpath("{}_aggregated_district_unique_devices.csv".format(slug_)), index=False)
    else:
        with open(result_loc_.parent.joinpath('error_log.log'), 'a') as f:
            f.write(state_ + 'devices ' + str(response.status_code) + response.text)
        exit(1)


# TODO: Remove DIKSHA specific filters from query
def district_plays(result_loc_, date_, query_, state_):
    """
    compute content plays per district over the week for the state
    :param result_loc_: pathlib.Path object to store resultant CSV at.
    :param date_: datetime object to pass query and path
    :param query_: json template for druid query
    :param state_: state to be used in query
    :return: None
    """
    slug_ = result_loc_.name
    start_date = date_ - timedelta(days=7)
    with open(file_path.parent.joinpath('resources').joinpath(query_)) as f:
        query = f.read()
    query = query.replace('state_name', state_)
    query = query.replace('start_date', datetime.strftime(start_date, '%Y-%m-%dT00:00:00+00:00'))
    query = query.replace('end_date', datetime.strftime(date_, '%Y-%m-%dT00:00:00+00:00'))
    response = requests.request("POST", url, data=query, headers=headers)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return
        data = []
        for response in response.json():
            data.append(response['event'])
        df = pd.DataFrame(data).fillna('Unknown')
        df.to_csv(result_loc_.parent.joinpath("{}_district_plays.csv".format(slug_)), index=False)
        post_data_to_blob(result_loc_.parent.joinpath("{}_district_plays.csv".format(slug_)), backup=True)
        df = df.join(city_district[city_district['state'] == state_].set_index('City'), on='City', how='left').fillna(
            'Unknown').groupby(['District', 'Platform'])['Number of Content Plays'].sum().reset_index()
        df.to_csv(result_loc_.parent.joinpath("{}_aggregated_district_content_plays.csv".format(slug_)), index=False)
    else:
        with open(result_loc_.parent.joinpath('error_log.log'), 'a') as f:
            f.write(state_ + 'plays ' + str(response.status_code) + response.text)
        exit(1)


# TODO: Remove DIKSHA specific filters from query
def district_scans(result_loc_, date_, query_, state_):
    """
    compute scans for a district over the week for the state
    :param result_loc_: pathlib.Path object to store resultant CSV at.
    :param date_: datetime object to be passed to the query and path
    :param query_: json template for druid query
    :param state_: state to be used in query
    :return: None
    """
    slug_ = result_loc_.name
    start_date = date_ - timedelta(days=7)
    with open(file_path.parent.joinpath('resources').joinpath(query_)) as f:
        query = f.read()
    query = query.replace('state_name', state_)
    query = query.replace('start_date', datetime.strftime(start_date, '%Y-%m-%dT00:00:00+00:00'))
    query = query.replace('end_date', datetime.strftime(date_, '%Y-%m-%dT00:00:00+00:00'))
    response = requests.request("POST", url, data=query, headers=headers)
    if response.status_code == 200:
        if len(response.json()) == 0:
            return
        data = []
        for response in response.json():
            data.append(response['event'])
        df = pd.DataFrame(data).fillna('Unknown')
        df.to_csv(result_loc_.parent.joinpath("{}_district_scans.csv".format(slug_)), index=False)
        post_data_to_blob(result_loc_.parent.joinpath("{}_district_scans.csv".format(slug_)), backup=True)
        df = df.join(city_district[city_district['state'] == state_].set_index('City'), on='City', how='left').fillna(
            'Unknown').groupby(['District', 'Platform'])['Number of QR Scans'].sum().reset_index()
        df.to_csv(result_loc_.parent.joinpath("{}_aggregated_district_qr_scans.csv".format(slug_)), index=False)
    else:
        with open(result_loc_.parent.joinpath('error_log.log'), 'a') as f:
            f.write(state_ + 'scans ' + str(response.status_code) + response.text)
        exit(1)


def merge_metrics(result_loc_, date_):
    """
    merge all the metrics
    :param result_loc_: pathlib.Path object to store resultant CSV at.
    :param date_: datetime object to be used in path
    :return: None
    """
    slug_ = result_loc_.name
    try:
        devices_df = pd.read_csv(
            result_loc_.parent.joinpath("{}_aggregated_district_unique_devices.csv".format(slug_))).set_index(
            ['District', 'Platform'])
    except FileNotFoundError:
        devices_df = pd.DataFrame([], columns=['District', 'Platform', 'Unique Devices']).set_index(
            ['District', 'Platform'])
    try:
        plays_df = pd.read_csv(
            result_loc_.parent.joinpath("{}_aggregated_district_content_plays.csv".format(slug_))).set_index(
            ['District', 'Platform'])
    except FileNotFoundError:
        plays_df = pd.DataFrame([], columns=['District', 'Platform', 'Number of Content Plays']).set_index(
            ['District', 'Platform'])
    try:
        scans_df = pd.read_csv(
            result_loc_.parent.joinpath("{}_aggregated_district_qr_scans.csv".format(slug_))).set_index(
            ['District', 'Platform'])
    except FileNotFoundError:
        scans_df = pd.DataFrame([['', '', 0]], columns=['District', 'Platform', 'Number of QR Scans']).set_index(
            ['District', 'Platform'])
    district_df = devices_df.join(scans_df, how='outer').join(plays_df, how='outer').reset_index().pivot(
        index='District', columns='Platform')
    district_df = district_df.join(district_df.sum(level=0, axis=1))
    district_df.columns = [col[0] + ' on ' + col[1].split('.')[-1] if isinstance(col, tuple) else 'Total ' + col for col
                           in district_df.columns]
    district_df['Data as on Last day (Sunday) of the week'] = datetime.strftime(date_ - timedelta(days=1), '%d/%m/%Y')
    district_df = district_df.reset_index()
    district_df.index = [pd.to_datetime(district_df['Data as on Last day (Sunday) of the week'], format='%d/%m/%Y'),
                         district_df['District']]
    for c in ['Unique Devices on portal', 'Unique Devices on app', 'Total Unique Devices',
              'Number of QR Scans on portal', 'Number of QR Scans on app', 'Total Number of QR Scans',
              'Number of Content Plays on portal', 'Number of Content Plays on app', 'Total Number of Content Plays']:
        if c not in district_df.columns:
            district_df[c] = 0
    try:
        get_data_from_blob(
            result_loc_.parent.parent.parent.joinpath("portal_dashboards", slug_, "aggregated_district_data.csv"))
        blob_data = pd.read_csv(
            result_loc_.parent.parent.parent.joinpath("portal_dashboards", slug_, "aggregated_district_data.csv"))
        blob_data.index = [pd.to_datetime(blob_data['Data as on Last day (Sunday) of the week'], format='%d/%m/%Y'),
                           blob_data['District']]
    except AzureMissingResourceHttpError:
        blob_data = pd.DataFrame()
    except FileNotFoundError:
        blob_data = pd.DataFrame()
    district_df = pd.concat([blob_data, district_df], sort=True)
    district_df = district_df.sort_index().drop_duplicates(
        subset=['Data as on Last day (Sunday) of the week', 'District'], keep='last').fillna(0)
    district_df = district_df[
        ['Data as on Last day (Sunday) of the week', 'District', 'Unique Devices on app', 'Unique Devices on portal',
         'Total Unique Devices',
         'Number of QR Scans on app', 'Number of QR Scans on portal', 'Total Number of QR Scans',
         'Number of Content Plays on app', 'Number of Content Plays on portal', 'Total Number of Content Plays']]
    district_df.to_csv(
        result_loc_.parent.parent.parent.joinpath("portal_dashboards", slug_, "aggregated_district_data.csv"),
        index=False)
    create_json(result_loc_.parent.parent.parent.joinpath("portal_dashboards", slug_, "aggregated_district_data.csv"))
    post_data_to_blob(
        result_loc_.parent.parent.parent.joinpath("portal_dashboards", slug_, "aggregated_district_data.csv"))


parser = argparse.ArgumentParser()
parser.add_argument("data_store_location", type=str, help="data folder location")
parser.add_argument("Druid_hostname", type=str, help="Host address for Druid")
parser.add_argument("-execution_date", type=str, default=date.today().strftime("%d/%m/%Y"),
                    help="DD/MM/YYYY, optional argument for backfill jobs")
args = parser.parse_args()

file_path = Path(__file__)
result_path = Path(args.data_store_location).joinpath('district_reports')
result_path.mkdir(exist_ok=True)
analysis_date = datetime.strptime(args.execution_date, "%d/%m/%Y")
# TODO: Move city-district and state-slug mapping outside
tenant_info = pd.read_csv(file_path.parent.parent.joinpath('resources').joinpath('slug_state_mapping.csv'))
city_district = pd.read_csv(file_path.parent.parent.joinpath('resources').joinpath('city_district_mapping.csv')).fillna(
    'Unknown')
url = "{}druid/v2/".format(args.Druid_hostname)
headers = {
    'Content-Type': "application/json"
}
for ind, row in tenant_info.iterrows():
    state = row['state']
    print(state)
    result_path.joinpath(analysis_date.strftime('%Y-%m-%d')).mkdir(exist_ok=True)
    result_path.joinpath(analysis_date.strftime('%Y-%m-%d'), row['slug']).mkdir(exist_ok=True)
    path = result_path.joinpath(analysis_date.strftime('%Y-%m-%d'), row['slug'])
    if isinstance(state, str):
        district_devices(result_loc_=path, date_=analysis_date, query_='district_devices.json', state_=state)
        district_plays(result_loc_=path, date_=analysis_date, query_='district_plays.json', state_=state)
        district_scans(result_loc_=path, date_=analysis_date, query_='district_scans.json', state_=state)
        merge_metrics(result_loc_=path, date_=analysis_date)
