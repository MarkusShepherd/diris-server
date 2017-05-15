'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp */

dirisApp.controller('LoginController', function LoginController(
    $location,
    $log,
    $rootScope,
    $scope,
    blockUI,
    toastr,
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
                    throw 'There was an error logging in...';
                }

                $location.path('/overview').replace();
            }).catch(function (response) {
                var message = _.upperFirst(response.non_field_errors || response.message ||
                                           response.toString() || 'There was an error logging in...');

                $log.debug(response);
                $log.debug(message);

                toastr.error(message);

                blockUI.stop();
            });
    }; // login
}); // LoginController
