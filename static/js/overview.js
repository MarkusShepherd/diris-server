'use strict';

dirisApp.controller('OverviewController', function OverviewController(
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
        action = $routeParams.action,
        matchPromise,
        playerPromise;

    if (!player) {
        $location.path('/login');
        return;
    }

    $scope.currentPlayer = player;
    $rootScope.menuItems = [];

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $rootScope.refreshPath = '/overview/refresh';
    $rootScope.refreshReload = action === 'refresh';

    matchPromise = dataService.getMatches(action === 'refresh', true)
        .then(function (matches) {
            var status = {};
            $scope.matches = $.map(matches, function (match) {
                status[match.status] = true;
                return processMatch(match, player);
            });
            $scope.status = status;
            $log.debug('Matches:', $scope.matches);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    playerPromise = dataService.getPlayers(action === 'refresh', true)
        .then(function (players) {
            $scope.players = players;
            $log.debug('Players:', $scope.players);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
        });

    $q.all([matchPromise, playerPromise]).then(blockUI.stop);

    $scope.newMatch = function newMatch() {
        $location.path('/newmatch');
    };

}); // PlayerController
