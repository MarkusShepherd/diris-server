'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp, utils */

dirisApp.controller('MatchController', function MatchController(
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
        forceRefresh = _.now() >= dataService.getNextUpdate();

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
    }];
    $rootScope.refreshButton = true;

    dataService.getMatch(mPk, forceRefresh)
        .then(function (match) {
            $log.debug('Match:', match);
            $scope.match = match;
            $scope.round = match.currentRoundObj;
            $log.debug('Round:', $scope.round);
            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.players = {};
            _.forEach(players, function (player) {
                $scope.players[player.pk.toString()] = player;
            });
            dataService.setNextUpdate('_renew');
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the data - please try again later...');
        }).then(blockUI.stop);

    dataService.getImages(mPk, forceRefresh, true)
        .then(function (images) {
            $scope.images = {};
            _.forEach(images, function (img) {
                $scope.images[img.pk.toString()] = img;
            });
            $log.debug('Images:', $scope.images);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the data - please try again later...');
        });

    $scope.action = utils.roundAction;

    $scope.rematch = function rematch() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        var match = $scope.match,
            playerPks = _(match.players).without(player.pk).unshift(player.pk).value();

        dataService.createMatch(playerPks, match.total_rounds, match.timeout)
            .then(function (newMatch) {
                $log.debug(newMatch);
                $location.path('/accept/' + newMatch.pk);
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);
                blockUI.stop();
                toastr.error("There was an error when creating the match...");
            });
    };
}); // MatchController
