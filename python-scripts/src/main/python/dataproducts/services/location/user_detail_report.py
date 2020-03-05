"""
District wise segragation of User detail report
"""
import json
import sys, time
import os
import pandas as pd
import requests
import pdb
import shutil

from datetime import date, datetime
from pathlib import Path
from string import Template

from dataproducts.util.utils import create_json, get_data_from_blob, \
                            post_data_to_blob, push_metric_event

class UserDetailReport:
    def __init__(self, data_store_location, states):
        self.data_store_location = Path(data_store_location)
        self.states = states


    def init(self):
        result_loc = self.data_store_location.joinpath('location')
        for slug in self.states.split(","):
            slug = slug.strip()
            state_result_loc = result_loc.joinpath(slug)
            os.makedirs(state_result_loc, exist_ok=True)
            try:
                get_data_from_blob(state_result_loc.joinpath('validated-user-detail', '{}.csv'.format(slug)))
            except Exception as e:
                print("validated-user-detail not available for "+slug)
                continue
            try:
                get_data_from_blob(state_result_loc.joinpath('validated-user-detail-state', '{}.csv'.format(slug)))
            except Exception as e:
                print("validated-user-detail-state not available for "+slug)
            user_df = pd.read_csv(state_result_loc.joinpath('validated-user-detail', '{}.csv'.format(slug)))
            district_group = user_df.groupby('District name')
            os.makedirs(state_result_loc.joinpath('districts'), exist_ok=True)
            for district_name, user_data in user_df.groupby('District name'):
                user_data.to_csv(state_result_loc.joinpath('districts', district_name.lower()+".csv"), index=False)

            shutil.move(state_result_loc.joinpath('validated-user-detail-state', '{}.csv'.format(slug)),
                state_result_loc.joinpath('districts', 'validated-user-detail-state.csv'))
            shutil.make_archive(str(state_result_loc.joinpath('validated-user-detail', slug)),
                                'zip',
                                str(state_result_loc.joinpath('districts')))
            post_data_to_blob(state_result_loc.joinpath('validated-user-detail', '{}.zip'.format(slug)))