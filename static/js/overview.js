'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp */

dirisApp.controller('OverviewController', function OverviewController(
    $location,
    $log,
    $q,
    $rootScope,
    $scope,
    blockUI,
    toastr,
    dataService
) {
    var player = dataService.getLoggedInPlayer(),
        forceRefresh = _.now() >= dataService.getNextUpdate(),
        matchPromise,
        playerPromise;

    if (!player) {
        $location.path('/login');
        return;
    }

    $scope.currentPlayer = player;

    $rootScope.menuItems = [];
    $rootScope.refreshButton = true;

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    matchPromise = dataService.getMatches(forceRefresh, true)
        .then(function (matches) {
            var status = {};
            _.forEach(matches, function (match) {
                status[match.actionStatus] = true;
            });
            $scope.matches = _.map(matches);
            $scope.status = status;
            $log.debug('Matches:', matches);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the data - please try again later...');
        });

    playerPromise = dataService.getPlayers(forceRefresh, true)
        .then(function (players) {
            $scope.players = players;
            $log.debug('Players:', $scope.players);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
        });

    $q.all([matchPromise, playerPromise]).then(blockUI.stop);
}); // PlayerController
