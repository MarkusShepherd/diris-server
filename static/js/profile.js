'use strict';

dirisApp.controller('ProfileController', function ProfileController(
    $location,
    $log,
    $rootScope,
    $routeParams,
    $scope,
    blockUI,
    dataService
) {
    var player = dataService.getLoggedInPlayer(),
        pPk = $routeParams.pPk,
        action = $routeParams.action;

    if (!player) {
        $location.path('/login');
        return;
    }

    $scope.currentPlayer = player;
    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }];

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    if (!pPk) {
        pPk = player.pk;
    }

    if (!action) {
        action = pPk == player.pk ? 'edit' : 'view';
    }

    $rootScope.refreshPath = null;
    $rootScope.refreshReload = false;

    dataService.getPlayer(pPk)
        .then(function (player) {
            $scope.player = player;
            $log.debug('Player:', $scope.player);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
        }).then(blockUI.stop);

}); // ProfileController
