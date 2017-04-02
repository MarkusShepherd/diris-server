'use strict';

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
        blockUI.start();

        $log.debug($scope.player);

        dataService.registerPlayer($scope.player)
            .then(function () {
                $location.path('/overview/refresh');
            }).catch(function () {
                blockUI.stop();
                $scope.message = 'There was an error - player "' +
                    $scope.player.username + '" could not be registered.';
            });
    }; // register
}); // RegistrationController
