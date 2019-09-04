from django.core.management.base import BaseCommand
import os,logging
from bro.gmw import registration_request
from acacia.meetnet.models import Well
from xml.etree.ElementTree import ElementTree
logger = logging.getLogger(__name__)

KVK='73552739'
class Command(BaseCommand):
    args = ''
    help = 'Create BRO registration request'
    
    def add_arguments(self,parser):
        
        parser.add_argument('--well','-w',
                action='store',
                type = int,
                dest = 'pk',
                default = None,
                help = 'id of well')

    def handle(self, *args, **options):
        pk = options.get('pk', None)
        queryset = Well.objects.all()
        if pk:
            queryset = queryset.filter(pk=pk)
        for well in queryset:
            logger.info(well)
            request = registration_request(well,KVK) 
            tree = ElementTree(request)
            tree.write('{}.xml'.format(well.nitg or well.name),xml_declaration=True,encoding='utf-8')

