'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp */

dirisApp.controller('AcceptController', function AcceptController(
    $location,
    $log,
    $q,
    $rootScope,
    $routeParams,
    $scope,
    blockUI,
    toastr,
    dataService
) {
    var player = dataService.getLoggedInPlayer(),
        mPk = $routeParams.mPk;

    if (!player) {
        $location.search('dest', $location.path()).path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.currentPlayer = player;
    $scope.mPk = mPk;

    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }, {
        link: '#/chat/' + mPk,
        label: 'Chat',
        glyphicon: 'send'
    }];
    $rootScope.refreshButton = false;

    dataService.getMatch(mPk)
        .then(function (match) {
            $scope.match = match;
            $scope.timeout = _.toInteger(match.timeout / 3600);
            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.players = {};
            _.forEach(players, function (player) {
                $scope.players[player.pk] = player;
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the data - please try again later...');
        }).then(blockUI.stop);

    $scope.respond = function respond(accept) {
        accept = !!accept;

        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        $q(function (resolve) {
            if (accept) {
                resolve(1);
            } else {
                navigator.notification.confirm(
                    'Are you sure you want to decline the invitation?',
                    resolve,
                    'Decline invitation',
                    ['Decline', 'Cancel']
                );
            }
        }).then(function (buttonIndex) {
            if (buttonIndex === 1) {
                return dataService.respondToInvitation(mPk, accept);
            }
            return false;
        }).then(function (response) {
            if (!response) {
                $log.debug('canceled declining invitation');
                blockUI.stop();
            } else {
                if (!accept) {
                    dataService.removeMatch(mPk);
                }
                $location.path('/overview');
            }
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            blockUI.stop();
            toastr.error('There was an error...');
        });
    };
}); // AcceptController
