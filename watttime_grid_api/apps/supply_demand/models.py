from django.db import models
from apps.gridentities.models import FuelType
from apps.griddata.models import BaseObservation, BaseUnboundObservation, DataPoint
import logging


logger = logging.getLogger(__name__)


class Load(BaseObservation):
    DEFAULT_UNITS = 'MW'


class TieFlow(BaseUnboundObservation):
    # source data point
    dp_source = models.ForeignKey(DataPoint, related_name='outflow')

    # destination data point
    dp_dest = models.ForeignKey(DataPoint, related_name='inflow')

    DEFAULT_UNITS = 'MW'


class Generation(models.Model):
    # generation source type
    fuel = models.ForeignKey(FuelType)

    # generation source type
    mix = models.ForeignKey(DataPoint, related_name='genmix')

    # how much power was generated
    gen_MW = models.FloatField()
    
    class Meta:
        unique_together = ('fuel', 'mix')
    
    def __str__(self):
        return '%s: %.1f MW' % (self.fuel, self.gen_MW)
