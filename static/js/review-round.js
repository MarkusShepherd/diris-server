'use strict';

dirisApp.controller('ReviewRoundController', function ReviewRoundController(
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
        mPk = $routeParams.mPk,
        rNo = $routeParams.rNo,
        matchPromise,
        imagePromise;

    if (!player) {
        $location.path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.mPk = mPk;
    $scope.rNo = rNo;

    $scope.currentPlayer = player;
    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }, {
        link: '#/match/' + mPk,
        label: 'Match',
        glyphicon: 'knight'
    }];
    $rootScope.refreshPath = null;
    $rootScope.refreshReload = false;

    matchPromise = dataService.getMatch(mPk)
        .then(function (match) {
            $scope.match = match;
            $scope.round = match.rounds[rNo - 1];
            $log.debug('current round', $scope.round);

            if ($scope.round.status === 's' || $scope.round.status === 'o') {
                $location.path('/image/' + mPk + '/' + rNo).replace();
                return;
            }

            if ($scope.round.status === 'v') {
                $location.path('/vote/' + mPk + '/' + rNo).replace();
                return;
            }

            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.players = {};
            _.forEach(players || [], function (player) {
                $scope.players[player.pk.toString()] = player;
            });
            $log.debug('players in match:', $scope.players);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    imagePromise = dataService.getImages(mPk, true, true)
        .then(function (images) {
            $scope.images = {};
            _.forEach(images, function (img) {
                $scope.images[img.pk.toString()] = img;
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    $q.all([matchPromise, imagePromise]).then(blockUI.stop);

    $scope.filterValues = function filterValues(items, value) {
        var result = [];
        _.forEach(items, function (v, k) {
            if (v == value) {
                result.push(k);
            }
        });
        return result;
    };

    $scope.filterOutKey = function filterOutKey(items, key) {
        var result = [];
        _.forEach(items, function (v, k) {
            if (k != key) {
                result.push(v);
            }
        });
        return result;
    };

});
