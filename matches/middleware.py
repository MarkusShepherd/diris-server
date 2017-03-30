# -*- coding: utf-8 -*-

'''middleware'''

# Orignal version taken from http://www.djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified by: Shwagroo Team and Gun.io
# See https://gun.io/blog/fast-as-fuck-django-part-1-using-a-profiler/
# Modified to use cProfile: Markus Shepherd

import cProfile
import pstats
import StringIO

class ProfileMiddleware(object):
    def process_request(self, request):
        if 'prof' in request.GET:
            self.prof = cProfile.Profile()
            self.prof.enable()

    def process_response(self, request, response):
        if 'prof' in request.GET:
            self.prof.disable()
            print request
            s = StringIO.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(self.prof, stream=s).sort_stats(sortby)
            ps.print_stats(.1, 100)
            print s.getvalue()

        return response
