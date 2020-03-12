# -*- coding: utf-8 -*-
'''
Created on Sep 27, 2019

@author: theo
'''

import re 
import logging
import pandas as pd

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from acacia.meetnet.models import Datalogger, LoggerDatasource, LoggerPos
from StringIO import StringIO
import binascii
from acacia.meetnet.actions import make_wellcharts
from acacia.data.models import SourceFile
import pytz
from acacia.meetnet.util import recomp

logger = logging.getLogger(__name__)
    
class Command(BaseCommand):
    help = 'Import Ellitrack cluster dump'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        admin = User.objects.get(username='theo')
        wells = set()
        tz=pytz.timezone('Europe/Amsterdam')
        for fname in files:
            logger.info('Importing data from {}'.format(fname))
            df = pd.read_excel(fname,index_col=0,na_values=['-'])
            nrows, ncols = df.shape
            span = [tz.localize(df.index.min()), tz.localize(df.index.max())]
            start, stop = span
            logger.info('{} loggers found'.format(ncols))
            logger.info('count = {}, start = {}, stop = {}.'.format(nrows, start, stop))
            screens = set()
            for col in df.columns:
                logger.info(col)
                pattern = r'(\d+):\s?(.+)\s-\s(\w+)'
                match = re.match(pattern,col)
                if not match:
                    raise ValueError('column name has wrong format: {}'.format(col))
                serial = match.group(1)
                #peilbuis = match.group(2)
                name = match.group(3)
                series = df[col] 
                try:
                    datalogger = Datalogger.objects.get(serial=serial)
                    datasource = LoggerDatasource.objects.get(logger=datalogger)
                    io = StringIO()
                    io.write('Datum\t{}\n'.format(name))
                    series.to_csv(io,sep='\t',header=False)
                    contents = io.getvalue()
                    crc = abs(binascii.crc32(contents))
                    sourcefile = datasource.sourcefiles.filter(crc=crc).first()
                    if sourcefile:
                        logger.warning('Skipped: sourcefile already exists')
                    else:
                        filename = 'Export_{}_{}_{:%Y%m%d}_{:%Y%m%d}.csv'.format(serial,name,start,stop)
                        sourcefile = SourceFile(name=filename,datasource=datasource,user=admin,crc=crc)
                        sourcefile.file.save(name=filename, content=io, save=True)
                except Exception as ex:
                    logger.error('Cannot create sourcefile for logger {}: {}'.format(serial,ex))
                
                # find out where logger is
                # we could use the name from the header, but this is not equal to the id of the screen in the database
                query = LoggerPos.objects.filter(logger=datalogger)
                pos = None
                if query.count() == 1:
                    pos = query.first()
                else:
                    # TODO: klopt niet, de if-else hieronder
                    query1 = query.filter(start_date__range=span)
                    if query1.count() == 1:
                        pos = query1.first()
                    else:
                        query2 = query.filter(end_date__range=span)
                        if query2.count() == 1:
                            pos = query2.first()
                if pos is None:
                    logger.error('Cannot find installation for logger {}'.format(serial))
                    continue
                pos.files.add(sourcefile)
                screens.add(pos.screen)

            logger.info('File import completed')
            if len(screens) > 0:
                logger.info('Updating time series')
                for screen in screens:
                    series = screen.find_series()
                    if series:
                        logger.info(series)
                        recomp(screen, series, start)
                        wells.add(screen.well)
        if len(wells)>0:
            logger.info('Updating well charts')
            make_wellcharts(None,None,wells)
        logger.info('Done.')