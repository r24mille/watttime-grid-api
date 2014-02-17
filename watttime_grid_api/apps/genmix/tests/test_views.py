from rest_framework import status
from rest_framework.test import APITestCase
from apps.gridentities.models import BalancingAuthority
from apps.griddata.models import DataSeries
from datetime import datetime, timedelta
import pytz


class GenMixAPITest(APITestCase):
    fixtures = ['isos.json']

    def setUp(self):
        self.base_url = '/api/v1'
        now = pytz.utc.localize(datetime.utcnow())
        tomorrow = now + timedelta(days=1)
        yesterday = now - timedelta(days=1)
        self.isne_true = DataSeries.objects.create(ba=BalancingAuthority.objects.get(abbrev='ISNE'),
                                  series_type=DataSeries.HISTORICAL)
        self.ciso_forecast = DataSeries.objects.create(ba=BalancingAuthority.objects.get(abbrev='CISO'),
                                  series_type=DataSeries.BEST)
        for ds in [self.isne_true, self.ciso_forecast]:
            for ts in [now, yesterday, tomorrow]:
                ds.datapoints.create(timestamp=ts)
        
    def _run_get(self, url, data, n_expected):
        """boilerplate for testing status and number of objects in get requests"""
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), n_expected)        
        return response
        
    def test_get(self):
        """simple get should find the two objects created in setUp"""
        url = self.base_url + '/genmix/'
        self._run_get(url, {}, 2)
                         
    def test_get_detail(self):
        """detail returns object with correct data"""
        url = self.base_url + '/genmix/1/'
        response = self._run_get(url, {}, 3)
        
        # correct field names
        for field in ['datapoints', 'ba', 'series_type']:
            self.assertIn(field, response.data.keys())
            
        # correct number of datapoints
        self.assertEqual(len(response.data['datapoints']), 3)
        
    def test_datapoint_content(self):
        url = self.base_url + '/genmix/1/'
        response = self._run_get(url, {}, 3)
        
        # test content of datapoints
        for dp in response.data['datapoints']:
            for field in ['timestamp', 'created_at', 'genmix', 'quality', 'url']:
                self.assertIn(field, dp.keys())
                