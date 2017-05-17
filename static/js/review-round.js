'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp, utils */

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
        forceRefresh = _.now() >= dataService.getNextUpdate();

    if (!player) {
        $location.path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.currentPlayer = player;
    $scope.mPk = mPk;
    $scope.rNo = rNo;

    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }, {
        link: '#/match/' + mPk,
        label: 'Match',
        glyphicon: 'knight'
    }];
    $rootScope.refreshButton = true;

    dataService.getMatch(mPk, forceRefresh, true)
        .then(function (match) {
            var round = match.rounds[rNo - 1],
                action = utils.roundAction(round);

            if (action !== 'review') {
                $location.path('/' + action + '/' + mPk + '/' + rNo).replace();
                return;
            }

            $scope.match = match;
            $scope.round = round;

            $scope.otherDetails = _.filter(round.details, function (details) {
                return details.image && details.player !== round.storyteller;
            });
            $scope.otherDetailsSize = _.size($scope.otherDetails);

            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.players = {};
            _.forEach(players || [], function (player) {
                $scope.players[player.pk.toString()] = player;
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        }).then(blockUI.stop);

    dataService.getImages(mPk, forceRefresh, true)
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
});
