'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp */

dirisApp.controller('NewMatchController', function NewMatchController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    toastr,
    dataService,
    MINIMUM_PLAYER,
    MAXIMUM_PLAYER,
    STANDARD_TIMEOUT
) {
    var player = dataService.getLoggedInPlayer();

    if (!player) {
        $location.path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.currentPlayer = player;
    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }];
    $rootScope.refreshPath = null;
    $rootScope.refreshReload = false;

    dataService.getPlayers()
        .then(function (players) {
            _.forEach(players, function (p) {
                p.selected = false;
            });
            $scope.playersArray = _(players).map().reject({pk: player.pk}).value();
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the player data...');
        }).then(blockUI.stop);

    $scope.selected = {};
    $scope.roundsPerPlayer = 2;
    $scope.numPlayers = 1;
    $scope.minimumPlayer = MINIMUM_PLAYER;
    $scope.maximumPlayer = MAXIMUM_PLAYER;
    $scope.timeout = _.toInteger(STANDARD_TIMEOUT / 3600);

    $scope.addPlayer = function addPlayer(p) {
        if (p.pk === player.pk) {
            $log.debug('added the current player');
            return;
        }

        p.selected = true;
        $scope.selected[p.pk.toString()] = p;
        $scope.numPlayers = _.size($scope.selected) + 1;

        if ($scope.createForm.roundsPerPlayer.$pristine &&
                $scope.numPlayers >= MINIMUM_PLAYER && $scope.numPlayers <= MAXIMUM_PLAYER) {
            $scope.roundsPerPlayer = _.toInteger(MAXIMUM_PLAYER / $scope.numPlayers);
        }
    };

    $scope.removePlayer = function removePlayer(p) {
        p.selected = false;
        delete $scope.selected[p.pk.toString()];
        $scope.numPlayers = _.size($scope.selected) + 1;

        if ($scope.createForm.roundsPerPlayer.$pristine &&
                $scope.numPlayers >= MINIMUM_PLAYER && $scope.numPlayers <= MAXIMUM_PLAYER) {
            $scope.roundsPerPlayer = _.toInteger(MAXIMUM_PLAYER / $scope.numPlayers);
        }
    };

    $scope.createMatch = function createMatch() {
        var playerPks,
            timeout,
            totalRounds;

        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        playerPks = _(_.keys($scope.selected)).without(player.pk).unshift(player.pk).value();

        if (_.size(playerPks) < MINIMUM_PLAYER) {
            blockUI.stop();
            toastr.error('Please select at least ' + (MINIMUM_PLAYER - 1) + ' players to invite to the match!');
            return;
        }

        if (_.size(playerPks) > MAXIMUM_PLAYER) {
            blockUI.stop();
            toastr.error('Please select no more than ' + (MAXIMUM_PLAYER - 1) + ' players to invite to the match!');
            return;
        }

        totalRounds = _.size(playerPks) * $scope.roundsPerPlayer;
        timeout = $scope.timeout * 3600;

        dataService.createMatch(playerPks, totalRounds, timeout)
            .then(function (match) {
                $log.debug(match);
                $location.path('/overview');
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);
                blockUI.stop();
                toastr.error("There was an error when creating the match...");
            });
    }; // createMatch

}); // NewMatchController
