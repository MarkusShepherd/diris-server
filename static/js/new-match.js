'use strict';

dirisApp.controller('NewMatchController', function NewMatchController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    toastr,
    dataService
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
            $scope.players = players;
            $scope.playersArray = $.map(players, function (p) { return p; });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the player data...');
        }).then(blockUI.stop);

    $scope.selected = {};
    $scope.numPlayers = 0;
    $scope.roundsPerPlayer = 2;

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

        blockUI.start();

        $.each($scope.selected, function (pk) {
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

        if (playerPks.length < 4) {
            blockUI.stop();
            toastr.error("Please select at least 3 players to invite to the match!");
            return;
        }

        dataService.createMatch(playerPks)
            .then(function (match) {
                $log.debug(match);
                $location.path('/overview');
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);
                toastr.error("There was an error when creating the match...");
                blockUI.stop();
            });
    }; // createMatch

}); // NewMatchController
