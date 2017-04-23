'use strict';

dirisApp.controller('NewMatchController', function NewMatchController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    toastr,
    dataService,
    MINIMUM_PLAYER,
    MAXIMUM_PLAYER
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
            _.forEach(players, function (player) {
                player.selected = false;
            });
            $scope.players = players;
            $scope.playersArray = _.map(players);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the player data...');
        }).then(blockUI.stop);

    $scope.selected = {};
    $scope.numPlayers = 0;
    $scope.roundsPerPlayer = 2;
    $scope.minimumPlayer = MINIMUM_PLAYER;
    $scope.maximumPlayer = MAXIMUM_PLAYER;

    $scope.addPlayer = function addPlayer(p) {
        p.selected = true;
        $scope.selected[p.pk.toString()] = p;
        $scope.numPlayers = $scope.numPlayers + 1;
    };

    $scope.removePlayer = function removePlayer(p) {
        p.selected = false;
        delete $scope.selected[p.pk.toString()];
        $scope.numPlayers = $scope.numPlayers - 1;
    };

    $scope.createMatch = function createMatch() {
        var playerPks = [],
            includeCurrent = false;

        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        _.forEach($scope.selected, function (p, pk) {
            if (pk == player.pk) {
                includeCurrent = true;
                playerPks.unshift(pk);
            } else {
                playerPks.push(pk);
            }
        });

        if (!includeCurrent) {
            playerPks.unshift(player.pk);
        }

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

        dataService.createMatch(playerPks)
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
