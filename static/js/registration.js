'use strict';

/*jslint browser: true, nomen: true, todo: true */
/*global _, dirisApp */

dirisApp.controller('RegistrationController', function RegistrationController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    toastr,
    dataService
) {
    dataService.logout();

    blockUI.stop();

    $rootScope.menuItems = [];
    $rootScope.refreshButton = false;

    $scope.register = function register() {
        if ($scope.player.password !== $scope.repeat_password) {
            toastr.error("Passwords don't match");
            return;
        }

        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        $log.debug($scope.player);

        dataService.createPlayer($scope.player)
            .then(function () {
                dataService.setNextUpdate();
                $location.path('/overview');
            }).catch(function (response) {
                // TODO use details on fields if available
                var message = _.upperFirst(JSON.stringify(response) ||
                                           'There was an error - player "' +
                                           $scope.player.username + '" could not be registered.');

                $log.debug(response);
                $log.debug(message);

                toastr.error(message);

                blockUI.stop();
            });
    }; // register
}); // RegistrationController
