from django.test import TestCase
from apps.gridentities.models import BalancingAuthority
from apps.supply_demand.models import Generation, Load
from apps.carbon.models import Carbon
from apps.marginal.models import MOER, MOERAlgorithm, StructuralModelSet
from apps.etl.models import ETLJob
from apps.etl import tasks
from datetime import datetime


class TestUpdateGeneration(TestCase):
    fixtures = ['isos', 'gentypes']

    def set_up_moer(self):
        # structural model
        self.alg = MOERAlgorithm.objects.create(binner=MOERAlgorithm.TOTAL_GEN,
                                                predictor=MOERAlgorithm.BETA,
                                                name=MOERAlgorithm.SILEREVANS_GEN)
        ba = BalancingAuthority.objects.get(abbrev='CAISO')
        self.sset = StructuralModelSet.objects.create(ba=ba, algorithm=self.alg,
                                                        valid_after=datetime(1900,1,1,0,0))
        self.sset.models().create(beta1=1, min_value=1, max_value=1e10)


    def test_update_generation_default(self):
    	# test for blank slate
        self.assertEqual(Generation.objects.filter(mix__ba__abbrev='CAISO').count(), 0)
        self.assertEqual(ETLJob.objects.filter(args__contains='CAISO').count(), 0)
        self.assertEqual(Carbon.objects.filter(dp__ba__abbrev='CAISO').count(), 0)

        # run task
        tasks.update_generation('CAISO', latest=True)

        # test for side effects
        job = ETLJob.objects.filter(args__contains='CAISO').latest()
        if not job.success:
            print job.errors

        gens = Generation.objects.filter(mix__ba__abbrev='CAISO')
        self.assertEqual(len(job.errors), 0)
        self.assertTrue(job.success)
        self.assertEqual(job.datapoints.count(), 1)
        self.assertGreater(gens.count(), 0)
        self.assertEqual(Carbon.objects.filter(dp__ba__abbrev='CAISO').count(), 1)
        for gen in gens:
	        self.assertEqual(gen.mix.id, job.datapoints.first().id)
        self.assertEqual(MOER.objects.filter(dp__ba__abbrev='CAISO').count(), 0)

    def test_update_generation_moer_gen(self):
        """Updating generation with SILEREVANS_GEN should create MOER"""
        # test for blank slate
        self.assertEqual(Generation.objects.filter(mix__ba__abbrev='CAISO').count(), 0)
        self.assertEqual(ETLJob.objects.filter(args__contains='CAISO').count(), 0)
        self.assertEqual(Carbon.objects.filter(dp__ba__abbrev='CAISO').count(), 0)

        # set up model
        self.set_up_moer()

        # run task
        tasks.update_generation('CAISO', moer_alg_name=MOERAlgorithm.SILEREVANS_GEN, latest=True)

        # test for side effects
        job = ETLJob.objects.filter(args__contains='CAISO').latest()
        if not job.success:
            print job.errors

        moers = MOER.objects.filter(dp__ba__abbrev='CAISO')
        self.assertEqual(moers.count(), 1)
        for moer in moers:
            self.assertEqual(moer.dp.id, job.datapoints.first().id)
            self.assertEqual(moer.value, 1)

    def test_update_generation_moer_load(self):
        """Updating generation with SILEREVANS should not create MOER"""
        # test for blank slate
        self.assertEqual(Generation.objects.filter(mix__ba__abbrev='CAISO').count(), 0)
        self.assertEqual(ETLJob.objects.filter(args__contains='CAISO').count(), 0)
        self.assertEqual(Carbon.objects.filter(dp__ba__abbrev='CAISO').count(), 0)

        # set up model
        self.set_up_moer()

        # run task
        tasks.update_generation('CAISO', moer_alg_name=MOERAlgorithm.SILEREVANS, latest=True)

        # test for side effects
        job = ETLJob.objects.filter(args__contains='CAISO').latest()
        if not job.success:
            print job.errors

        moers = MOER.objects.filter(dp__ba__abbrev='CAISO')
        self.assertEqual(moers.count(), 0)


class TestUpdateLoad(TestCase):
    fixtures = ['isos']

    def set_up_moer(self):
        # structural model
        self.alg = MOERAlgorithm.objects.create(binner=MOERAlgorithm.TOTAL_LOAD,
                                                predictor=MOERAlgorithm.BETA,
                                                name=MOERAlgorithm.SILEREVANS)
        ba = BalancingAuthority.objects.get(abbrev='CAISO')
        self.sset = StructuralModelSet.objects.create(ba=ba, algorithm=self.alg,
                                                        valid_after=datetime(1900,1,1,0,0))
        self.sset.models().create(beta1=1, min_value=1, max_value=1e10)


    def test_update_load_default(self):
        # test for blank slate
        self.assertEqual(Load.objects.filter(dp__ba__abbrev='CAISO').count(), 0)
        self.assertEqual(ETLJob.objects.filter(args__contains='CAISO').count(), 0)

        # run task
        tasks.update_load('CAISO', latest=True)

        # test for side effects
        job = ETLJob.objects.filter(args__contains='CAISO').latest()
        if not job.success:
            print job.errors

        loads = Load.objects.filter(dp__ba__abbrev='CAISO')
        self.assertEqual(len(job.errors), 0)
        self.assertTrue(job.success)
        self.assertEqual(job.datapoints.count(), 1)
        self.assertEqual(loads.count(), 1)
        self.assertEqual(loads.first().dp.id, job.datapoints.first().id)
        self.assertEqual(MOER.objects.filter(dp__ba__abbrev='CAISO').count(), 0)

    def test_update_load_moer_load(self):
        """Updating load with SILEREVANS should create MOER"""
         # set up model
        self.set_up_moer()

        # run task
        tasks.update_load('CAISO', moer_alg_name=MOERAlgorithm.SILEREVANS, latest=True)

        # test for side effects
        job = ETLJob.objects.filter(args__contains='CAISO').latest()
        if not job.success:
            print job.errors

        moers = MOER.objects.filter(dp__ba__abbrev='CAISO')
        self.assertEqual(moers.count(), 1)
        for moer in moers:
            self.assertEqual(moer.dp.id, job.datapoints.first().id)
            self.assertEqual(moer.value, 1)

    def test_update_load_moer_gen(self):
        """Updating load with SILEREVANS_GEN should not create MOER"""
         # set up model
        self.set_up_moer()

        # run task
        tasks.update_load('CAISO', moer_alg_name=MOERAlgorithm.SILEREVANS_GEN, latest=True)

        # test for side effects
        job = ETLJob.objects.filter(args__contains='CAISO').latest()
        if not job.success:
            print job.errors

        moers = MOER.objects.filter(dp__ba__abbrev='CAISO')
        self.assertEqual(moers.count(), 0)
