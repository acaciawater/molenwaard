'''
Created on Sep 1, 2016

@author: theo
'''
from acacia.meetnet.views import NetworkView
from acacia.meetnet.models import Network, Well
from django.contrib.gis.gdal.srs import SpatialReference, CoordTransform 
from django.http.response import JsonResponse, HttpResponseServerError
from django.views.generic.detail import DetailView
import json
from django.conf import settings


#deprecated 
class GooleView(NetworkView):
    def get_context_data(self, **kwargs):
        context = NetworkView.get_context_data(self, **kwargs)
        context['maptype'] = 'SATELLITE'
        return context

    def get_object(self):
        return Network.objects.get(name = 'Molenwaard')
    
class HomeView(NetworkView):
    template_name = 'molenwaard/home.html'

    def get_context_data(self, **kwargs):
        context = NetworkView.get_context_data(self, **kwargs)
        options = {
            'center': [52.15478, 4.48565],
            'zoom': 12 }
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = json.dumps(options)
        return context

    def get_object(self):
        return Network.objects.first()

class PopupView(DetailView):
    """ returns html response for leaflet popup """
    model = Well
    template_name = 'meetnet/well_info.html'
    
def well_locations(request):
    """ return json response with well locations
    """
    result = []
    trans = None
    for p in Well.objects.all():
        try:
            pnt = p.location
            if trans is None:
                wgs84 = SpatialReference(4326)
                rdnew = SpatialReference(28992)
                trans = CoordTransform(rdnew,wgs84)
            pnt.transform(trans)
            result.append({'id': p.id, 'name': p.name, 'nitg': p.nitg, 'description': p.description, 'lon': pnt.x, 'lat': pnt.y})
        except Exception as e:
            return HttpResponseServerError(unicode(e))
    return JsonResponse(result,safe=False)
