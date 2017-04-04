'use strict';

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
        action = $routeParams.action,
        matchPromise,
        imagePromise;

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

    $rootScope.refreshPath = '/match/' + mPk + '/refresh';
    $rootScope.refreshReload = action === 'refresh';

    $scope.mPk = mPk;

    matchPromise = dataService.getMatch(mPk, action === 'refresh')
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
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    imagePromise = dataService.getImages(mPk, action === 'refresh', true)
        .then(function (images) {
            $scope.images = {};
            _.forEach(images, function (img) {
                $scope.images[img.pk.toString()] = img;
            });
            $log.debug('Images:', $scope.images);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    $q.all([matchPromise, imagePromise]).then(blockUI.stop);

}); // MatchController
