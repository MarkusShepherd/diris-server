# -*- coding: utf-8 -*-

'''middleware'''

# Orignal version taken from http://www.djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified by: Shwagroo Team and Gun.io
# See https://gun.io/blog/fast-as-fuck-django-part-1-using-a-profiler/
# Modified to use cProfile: Markus Shepherd

import cProfile
import logging
import pstats
import StringIO


class ProfileMiddleware(object):
    logger = logging.getLogger(__name__ + '.ProfileMiddleware')
    prof = None

    def process_request(self, request):
        if 'prof' in request.GET:
            self.prof = cProfile.Profile()
            self.prof.enable()

    def process_response(self, request, response):
        if 'prof' in request.GET:
            self.prof.disable()

            self.logger.debug(request)

            stream = StringIO.StringIO()
            stats = pstats.Stats(self.prof, stream=stream).sort_stats('cumulative')
            stats.print_stats(.1, 20)
            self.logger.debug(stream.getvalue())

            stream = StringIO.StringIO()
            stats = pstats.Stats(self.prof, stream=stream).sort_stats('tottime')
            stats.print_stats(.1, 20)
            self.logger.debug(stream.getvalue())

        return response
