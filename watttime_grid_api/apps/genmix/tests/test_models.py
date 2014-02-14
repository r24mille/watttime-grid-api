from django.test import TestCase
from django.db import IntegrityError
from django.db.transaction import TransactionManagementError
from apps.genmix.models import GenMix, Generation
from apps.gridentities.models import GridEntity
from datetime import datetime
import pytz


class TestGeneration(TestCase):
    fixtures = ['isos.json']

    def test_failing_create(self):
        self.assertRaises(IntegrityError, Generation.objects.create)
        
    def test_create_each_fuel(self):
        for (choice, verbose) in Generation.FUEL_CHOICES:
            Generation.objects.create(fuel=choice, gen_MW=100)

    def test_add_mix(self):
        gen = Generation.objects.create(fuel=Generation.FUEL_CHOICES[0][0], gen_MW=100)
        gen.mix.create(ge=GridEntity.objects.get(pk=1),
                       timestamp=datetime.now())


class TestGenMix(TestCase):
    fixtures = ['isos.json']
    def setUp(self):
        self.ge = GridEntity.objects.get(pk=1)

    def test_failing_create(self):
        self.assertRaises(IntegrityError, GenMix.objects.create)
        self.assertRaises(TransactionManagementError, GenMix.objects.create,
                          timestamp=pytz.utc.localize(datetime.utcnow()))
        self.assertRaises(TransactionManagementError, GenMix.objects.create,
                          ge=self.ge)
        
    def test_default_create(self):
        genmix = GenMix.objects.create(ge=self.ge,
                                       timestamp=pytz.utc.localize(datetime.utcnow()))
        self.assertEqual(genmix.confidence_type, GenMix.TRUE)
        self.assertEqual(genmix.sources.count(), 0)