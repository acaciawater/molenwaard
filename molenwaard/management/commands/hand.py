'''
Created on Dec 6, 2014

@author: theo
'''
import csv, datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
import pytz

from acacia.data.models import ProjectLocatie, MeetLocatie, ManualSeries
from acacia.meetnet.models import Well, Screen

class Command(BaseCommand):
    args = ''
    help = 'Importeer handpeilingen'
    def add_arguments(self, parser):
        parser.add_argument('-f','--file',
                action='store',
                dest = 'fname',
                default = None,
                help='CSV file met handpeilingen'
        )
        
    def handle(self, *args, **options):
        fname = options.get('fname')
        CET=pytz.timezone('Etc/GMT-1')
        user=User.objects.get(username='theo')
        if fname:
            with open(fname,'r') as f:
                reader = csv.DictReader(f, delimiter=',')
                for row in reader:
                    try:
                        name = row['Peilbuis']
                        well = Well.objects.get(name=name)
                        filt = int(row.get('Filter',1))
                        screen = well.screen_set.get(nr=filt)
                        ploc = well.ploc
                        name2= '%s/%03d' % (well.name, filt)
                        mloc = ploc.meetlocatie_set.get(name=name2)
                        datumtijd = row['Datum']
                        depth = row['Meting']
                        if depth:
                            depth = float(depth) / 100
                        else:
                            continue
                        if not screen.refpnt:
                            print 'Reference point for screen %s not available' % screen
                            continue
                        nap = screen.refpnt - depth
                        date = datetime.datetime.strptime(datumtijd,'%Y-%m-%d %H:%M')
                        date = CET.localize(date)
                        series_name = '%s HAND' % mloc.name
                        series,created = ManualSeries.objects.get_or_create(name=series_name,mlocatie=mloc,defaults={'description':'Handpeiling', 'timezone':'Etc/GMT-1', 'unit':'m NAP', 'type':'scatter', 'user':user})
                        pt, created = series.datapoints.update_or_create(date=date,defaults={'value': nap})
                        print screen, pt.date, pt.value
                    except Well.DoesNotExist:
                        print 'Well %s not found' % name
                    except Screen.DoesNotExist:
                        print 'Screen %s/%03d not found' % (name, filt)
                    except MeetLocatie.DoesNotExist:
                        print 'Meetlocatie %s/%03d not found' % (name, filt)
                    except Exception as e:
                        print e, name
                        