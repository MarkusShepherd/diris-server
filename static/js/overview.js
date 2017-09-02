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
        allMatches = {},
        matchPromise,
        playerPromise;

    function addMatches(matches) {
        _.assign(allMatches, matches);

        $scope.matches = _(allMatches).map().filter('pk').value();
        $scope.matchesRefreshButton = _.isUndefined(allMatches._nextPage);
        $scope.matchesNextPage = allMatches._nextPage;
        $scope.matchesPrevPage = allMatches._prevPage;
        $scope.status = {};

        _.forEach($scope.matches, function (match) {
            $scope.status[match.actionStatus] = true;

            dataService.getChatNumNew(match.pk)
                .then(function (numMessages) {
                    match.numMessages = numMessages;
                });
        });
    }

    if (!player) {
        $location.search('dest', $location.path()).path('/login');
        return;
    }

    $scope.currentPlayer = player;
    $scope.matchesRefreshButton = !forceRefresh;

    $rootScope.menuItems = [];
    $rootScope.refreshButton = true;

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    matchPromise = dataService.getMatches(forceRefresh, true)
        .then(addMatches)
        .catch(function (response) {
            $log.warn('error');
            $log.warn(response);
            toastr.error('There was an error fetching the data - please try again later...');
        });

    playerPromise = dataService.getPlayers(forceRefresh, true)
        .then(function (players) {
            $scope.players = players;
        }).catch(function (response) {
            $log.warn('error');
            $log.warn(response);
        });

    $q.all([matchPromise, playerPromise]).then(blockUI.stop);

    $scope.loadMore = function loadMore(page) {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        dataService.getMatches(true, true, page)
            .then(addMatches)
            .catch(function (response) {
                $log.warn('error');
                $log.warn(response);
                toastr.error('There was an error fetching the data - please try again later...');
            }).then(blockUI.stop);
    }; // loadMore
}); // PlayerController
