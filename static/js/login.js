'use strict';

/*jslint browser: true */
/*global dirisApp */

dirisApp.controller('LoginController', function LoginController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    dataService
) {
    var player = dataService.getLoggedInPlayer();

    if (player) {
        $location.path('/overview').replace();
        return;
    }

    blockUI.stop();

    $rootScope.menuItems = [];
    $rootScope.refreshButton = false;

    $scope.login = function login() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        dataService.getToken($scope.player.name, $scope.player.password)
            .then(function (token) {
                $log.debug('token:', token);
                if (!token) {
                    throw new Error('no token');
                }
                $location.path('/overview').replace();
            }).catch(function (response) {
                $log.debug(response);
                $scope.message = response.message || "There was an error...";
                blockUI.stop();
            });
    }; // login
}); // LoginController
