#!/usr/bin/env python3
import sys
import logging
import random

import curio
import ophyd
from ophyd import Component as Cpt, EpicsSignal, EpicsSignalRO

from caproto.benchmarking import set_logging_level
from caproto.curio.server import start_server
from caproto.curio.high_level_server import (pvproperty, PVGroup,
                                             pvfunction)
from caproto.curio.conversion import group_to_device

logger = logging.getLogger(__name__)


# Step 1: a caproto high-level server

class Group(PVGroup):
    'Example group of PVs, where the prefix is defined on instantiation'
    async def _exit(self, instance, value):
        logger.info('Server shutting down')
        sys.exit(0)

    exit = pvproperty(put=_exit, doc='Poke me to exit')

    @pvproperty
    async def random1(self, instance):
        'Random integer between 1 and 100'
        return random.randint(1, 100)

    @pvproperty
    async def random2(self, instance):
        'A nice random integer between 1000 and 2000'
        return random.randint(1000, 2000)

    @pvfunction(default=[0])
    async def get_random(self,
                         low: int=100,
                         high: int=1000) -> int:
        'A configurable random number'
        low, high = low[0], high[0]
        return random.randint(low, high)


# Step 2a: write supporting methods to make simple ophyd Devices (moved to
#          caproto.curio.conversion module)

# Step 2b: copy/pasting the auto-generated output (OK, slightly modified for
#                                                  PEP8 readability)

# Auto-generated Device from here on:
# -----------------------------------
class get_randomDevice(ophyd.Device):
    low = Cpt(EpicsSignal, 'low', doc="Parameter <class 'int'> low")
    high = Cpt(EpicsSignal, 'high', doc="Parameter <class 'int'> high")
    status = Cpt(EpicsSignalRO, 'Status', string=True,
                 doc="Parameter <class 'str'> status")
    retval = Cpt(EpicsSignalRO, 'Retval', doc="Parameter <class 'int'> retval")
    process = Cpt(EpicsSignal, 'Process',
                  doc="Parameter <class 'int'> Process")

    def call(self, low: int=100, high: int=1000):
        'A configurable random number'
        self.low.put(low, wait=True)
        self.high.put(high, wait=True)
        self.process.put(1, wait=True)
        status = self.status.get(use_monitor=False)
        retval = self.retval.get(use_monitor=False)
        if status != 'Success':
            raise RuntimeError(f'RPC function failed: {status}')
        return retval


class GroupDevice(ophyd.Device):
    get_random = Cpt(get_randomDevice, 'get_random:',
                     doc='A configurable random number')
    exit = Cpt(EpicsSignal, 'exit', doc='Poke me to exit')
    random1 = Cpt(EpicsSignal, 'random1',
                  doc='Random integer between 1 and 100')
    random2 = Cpt(EpicsSignal, 'random2',
                  doc='A nice random integer between 1000 and 2000')
# -------end autogenerated Devices---


if __name__ == '__main__':
    try:
        prefix = sys.argv[1]
    except IndexError:
        prefix = 'integration:'

    ioc = Group(prefix=prefix, macros={})

    print('import ophyd')
    print('from ophyd import Component as Cpt, EpicsSignal')

    print('# Auto-generated Device from here on:')
    print('# -----------------------------------')

    for line in group_to_device(ioc):
        print(line)

    print('# -------end autogenerated Devices---')

    # Step 3a: Run the server in the parent process

    set_logging_level(logging.INFO)
    logger.setLevel(logging.INFO)
    logging.basicConfig()

    logger.info('Starting up: prefix=%r', prefix)

    curio.run(start_server, ioc.pvdb)

    # Step 3b:
    # NOTE: run separately: caproto.ioc_examples.caproto_to_typhon
