from django.test import TestCase, Client
from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APITestCase
from apps.gridentities.models import BalancingAuthority, FuelType
from apps.griddata.models import DataPoint
from datetime import datetime, timedelta
from dateutil.parser import parse as dateutil_parse
import pytz


class TestDocs(TestCase):
    def test_docs(self):
        c = Client()
        response = c.get('/api/v1/docs/')
        self.assertEqual(response.status_code, 200)
        for test_str in ['django-rest-swagger']:
            self.assertIn(test_str, response.content)


class BAAPITest(APITestCase):
    fixtures = ['bageom.json']
    
    def setUp(self):
        self.base_url = '/api/v1'
        
    def test_get(self):
        url = self.base_url + '/balancing_authorities/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data),
                         BalancingAuthority.objects.count())
                         
    def test_filter(self):
        url = self.base_url + '/balancing_authorities/'
        
        queries = [({'abbrev': 'ISONE'}, 1),
                   ({'ba_type': 'ISO'}, 8),
                   ]
        for query, n_expected in queries:
            response = self.client.get(url, data=query)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), n_expected)
            
    def test_geofilter(self):
        url = self.base_url + '/balancing_authorities/'
        
        # Amherst
        point = Point(-72.5196616, 42.3722951)
        
        # formats
        formatted_points = [point.geojson, point.wkt]
        queries = [({'loc': frm}, 1) for frm in formatted_points]
        
        for query, n_expected in queries:
            response = self.client.get(url, data=query)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), n_expected)


class DataPointsAPITest(APITestCase):
    fixtures = ['bageom', 'gentypes', 'fuelcarbonintensities']

    def setUp(self):
        # set up times
        self.now = pytz.utc.localize(datetime.utcnow())
        self.tomorrow = self.now + timedelta(days=1)
        self.yesterday = self.now - timedelta(days=1)
        
        # create sample data points
        for ba in [BalancingAuthority.objects.get(abbrev='ISONE'),
                   BalancingAuthority.objects.get(abbrev='CAISO')]:
            for ts in [self.now, self.yesterday, self.tomorrow]:
                DataPoint.objects.create(timestamp=ts, ba=ba,
                                         market=DataPoint.RT5M, freq=DataPoint.FIVEMIN)
                DataPoint.objects.create(timestamp=ts, ba=ba,
                                         market=DataPoint.RT5M, freq=DataPoint.IRREGULAR)
                DataPoint.objects.create(timestamp=ts, ba=ba,
                                         market=DataPoint.RTHR, freq=DataPoint.HOURLY)
                                         
        # add sample gens to data points
        for dp in DataPoint.objects.all():
            dp.genmix.create(fuel=FuelType.objects.get(name='wind'), gen_MW=100)
            dp.genmix.create(fuel=FuelType.objects.get(name='natgas'), gen_MW=200)

        # number of expected objects of different types
        self.n_isos = 2
        self.n_times = 3
        self.n_at_time = 3
        self.n_gen = 2

        # set up routes
        self.base_url = '/api/v1/datapoints/'
        
    def _run_get(self, url, data, n_expected):
        """boilerplate for testing status and number of objects in get requests"""
        response = self.client.get(url, data=data)
        if response.status_code is not status.HTTP_200_OK:
            print response.data, url
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), n_expected)        
        return response
        
    def test_data_created(self):
        self.assertEqual(DataPoint.objects.all().count(),
                         self.n_isos*self.n_times*self.n_at_time)
        self.assertGreater(DataPoint.objects.all(), 1)
        
    def test_get(self):
        """get list"""
        url = self.base_url
        self._run_get(url, {}, self.n_isos*self.n_times*self.n_at_time)
                         
    def test_filter_ba_abbrev(self):
        """can filter by BA name"""
        url = self.base_url
        response = self._run_get(url, {'ba': 'CAISO'}, self.n_times*self.n_at_time) 
                    
        for dp in response.data:
            self.assertEqual(dp['ba'], 'CAISO')
        
    def test_filter_ba_loc(self):
        """can filter by location within BA"""
        url = self.base_url
        
        # Amherst
        geojson = { "type": "Point",
                   "coordinates": [ -72.5196616, 42.3722951 ] }
        response = self._run_get(url, {'loc': geojson}, self.n_times*self.n_at_time)
        
        for dp in response.data:
            self.assertEqual(dp['ba'], 'ISONE')
        
    def test_multifilter(self):
        """filters should act like AND"""
        pass
        
    def test_get_detail(self):
        """detail returns object with correct data"""
        pk = DataPoint.objects.all()[0].id
        url = self.base_url + '%d/' % pk
        response = self._run_get(url, {}, 8)
        
        # correct field names
        for field in ['ba', 'timestamp', 'genmix', 'carbon', 'created_at',
                      'url', 'freq', 'market']:
            self.assertIn(field, response.data.keys())
            
    def test_filter_start_iso(self):
        url = self.base_url
        
        # like '2006-10-25T14:30:59+00:00'
        dtstr = self.now.isoformat()

        # start time inclusive
        response = self._run_get(url, {'start_at': dtstr},
                                       self.n_isos*(self.n_times-1)*self.n_at_time)

        for dp in response.data:
            self.assertGreaterEqual(dp['timestamp'], self.now)

    def test_filter_start_day(self):
        url = self.base_url
        
        # like '2006-10-25'
        dtstr = self.now.strftime('%Y-%m-%d')

        # start time inclusive
        response = self._run_get(url, {'start_at': dtstr},
                                       self.n_isos*(self.n_times-1)*self.n_at_time)
        for dp in response.data:
            self.assertGreaterEqual(dp['timestamp'], self.now)

    def test_filter_start_hmz(self):
        url = self.base_url
        
        # like '2006-10-25T14:30+0000'
        dtstr = self.now.strftime('%Y-%m-%dT%H:%M%z')

        # start time inclusive
        response = self._run_get(url, {'start_at': dtstr},
                                       self.n_isos*(self.n_times-1)*self.n_at_time)
        for dp in response.data:
            self.assertGreaterEqual(dp['timestamp'], self.now)

    def test_filter_start_hmsz(self):
        url = self.base_url
        
        # like '2006-10-25T14:30:59+0000'
        dtstr = self.now.strftime('%Y-%m-%dT%H:%M:%S%z')
        
        # start time inclusive
        response = self._run_get(url, {'start_at': dtstr},
                                       self.n_isos*(self.n_times-1)*self.n_at_time)
        for dp in response.data:
            self.assertGreaterEqual(dp['timestamp'], self.now)

    def test_filter_end(self):
        url = self.base_url
        
        # end time inclusive
        response = self._run_get(url, {'end_at': self.now.isoformat()},
                                       self.n_isos*(self.n_times-1)*self.n_at_time)
        for dp in response.data:
            self.assertLessEqual(dp['timestamp'], self.now)
