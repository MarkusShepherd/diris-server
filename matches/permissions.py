# -*- coding: utf-8 -*-

'''permissions'''

from __future__ import absolute_import, division, print_function, unicode_literals, with_statement

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .utils import get_player

class IsOwnerOrCreateAndRead(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS + ('POST',):
            return True

        player = get_player(request)
        pk = obj.owner_id if hasattr(obj, 'owner_id') else obj.pk

        return player and player.pk == pk
