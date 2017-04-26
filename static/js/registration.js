'use strict';

/*jslint browser: true */
/*global dirisApp */

dirisApp.controller('RegistrationController', function RegistrationController(
    $location,
    $log,
    $scope,
    blockUI,
    dataService
) {
    dataService.logout();

    blockUI.stop();

    $scope.register = function register() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        $log.debug($scope.player);

        dataService.createPlayer($scope.player)
            .then(function () {
                $location.path('/overview/refresh');
            }).catch(function () {
                blockUI.stop();
                $scope.message = 'There was an error - player "' +
                    $scope.player.username + '" could not be registered.';
            });
    }; // register
}); // RegistrationController
