from django.test import TestCase
from django.db import IntegrityError
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from apps.gridentities.models import BalancingAuthority, FuelType, PowerPlant


class BATest(TestCase):
    def test_create(self):
        """test creation of every choice"""
        for (choice, verbose) in BalancingAuthority.BA_TYPE_CHOICES:
            ba = BalancingAuthority.objects.create(ba_type=choice,
                                                   name='test '+verbose,
                                                   abbrev=choice)
            self.assertIsNotNone(ba)
            
    def test_choices(self):
        """test that all expected choices exist"""
        choices = set(x[0] for x in BalancingAuthority.BA_TYPE_CHOICES)
        expected_choices = set([BalancingAuthority.ISO, BalancingAuthority.BA])
        self.assertEqual(choices, expected_choices)
        
    def test_unique_abbrev(self):
        choice, verbose = BalancingAuthority.BA_TYPE_CHOICES[0]
        ba = BalancingAuthority.objects.create(ba_type=choice,
                                               name='test 1',
                                               abbrev=choice)
        self.assertRaises(IntegrityError, BalancingAuthority.objects.create,
                          ba_type='test', name='test 2', abbrev=choice)
        
    def test_load(self):
        # like loading data from a fixture
        from apps.gridentities import load
        load.run_balancing_authority()
        
        # test number loaded
        self.assertEqual(BalancingAuthority.objects.all().count(), 93)
        
        # test service areas created
        for ba in BalancingAuthority.objects.all():
            self.assertGreater(ba.geom.num_points, 1)
            self.assertIn(ba.ba_type, dict(ba.BA_TYPE_CHOICES).keys())
            
    def test_service_area_contains(self):
        from apps.gridentities import load
        load.run_balancing_authority()

        # service area contains its own centroid
        ba = BalancingAuthority.objects.get(abbrev='ISONE')
        poly = ba.geom
        self.assertTrue(poly.contains(poly.centroid))
        
    def test_service_area_filter_contains(self):
        from apps.gridentities import load
        load.run_balancing_authority()
        
        points = [BalancingAuthority.objects.get(abbrev='ISONE').geom.centroid,
                  Point(-72.5196616, 42.3722951) # Amherst
                  ]

        # BA's service area contains its own centroid
        for point in points:
            containers = BalancingAuthority.objects.filter(geom__contains=point)
            self.assertEqual(containers.count(), 1)
            self.assertEqual(containers[0].abbrev, 'ISONE')
        

class FuelTest(TestCase):
    def test_full_create(self):
        fuel = FuelType(name='coal', description='coal-fired thermal power plant')
        self.assertIsNotNone(fuel)

    def test_default_create(self):
        fuel = FuelType(name='coal')
        self.assertEqual(fuel.description, '')
        
    def test_unique_name(self):
        fuel = FuelType.objects.create(name='coal')
        self.assertRaises(IntegrityError, FuelType.objects.create, name='coal')
        
        
class PowerPlantTest(TestCase):
    def test_null_create(self):
        pp = PowerPlant()
        self.assertEqual(pp.code, '')
        self.assertEqual(pp.coord, None)
        
    def test_load(self):
        # like loading data from a fixture
        from apps.gridentities import load
        load.run_power_plant(verbose=False)
        self.assertEqual(PowerPlant.objects.all().count(), 1324)
        
    def test_nearest(self):
        # load
        from apps.gridentities import load
        load.run_power_plant(verbose=False)
        
        # Boston
        point = Point(-71.03, 42.21)
        
        # number nearby
        nearby_pps = PowerPlant.objects.filter(coord__distance_lt=(point, D(mi=100)))
        self.assertEqual(nearby_pps.count(), 21)
        
        # sort by distance
        nearby_pps_sorted = nearby_pps.distance(point).order_by('distance')
        self.assertLess(nearby_pps_sorted[0].distance, nearby_pps_sorted[1].distance)

        # identity of closest
        self.assertEqual(nearby_pps_sorted[0].code, '6049')
        

