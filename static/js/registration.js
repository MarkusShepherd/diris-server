'use strict';

/*jslint browser: true */
/*global dirisApp */

dirisApp.controller('RegistrationController', function RegistrationController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    dataService
) {
    dataService.logout();

    blockUI.stop();

    $rootScope.menuItems = [];
    $rootScope.refreshButton = false;

    $scope.register = function register() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        $log.debug($scope.player);

        dataService.createPlayer($scope.player)
            .then(function () {
                dataService.setNextUpdate();
                $location.path('/overview');
            }).catch(function () {
                blockUI.stop();
                $scope.message = 'There was an error - player "' +
                    $scope.player.username + '" could not be registered.';
            });
    }; // register
}); // RegistrationController
