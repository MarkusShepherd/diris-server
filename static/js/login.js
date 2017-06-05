'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp */

dirisApp.controller('LoginController', function LoginController(
    $location,
    $log,
    $q,
    $rootScope,
    $scope,
    blockUI,
    toastr,
    dataService
) {
    function login(username, password) {
        var message;

        username = username || $scope.player.name;
        password = password || $scope.player.password;

        if (!username || !password) {
            message = 'Username and password are required for login';
            $log.debug(message);
            toastr.error(message);
            return $q.reject();
        }

        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        return dataService.getToken(username, password)
            .then(function (token) {
                $log.debug('token:', token);

                if (!token) {
                    throw 'There was an error logging in...';
                }

                $location.path('/overview').replace();
            }).catch(function (response) {
                message = _.upperFirst(response.non_field_errors || response.message ||
                                           response.toString() || 'There was an error logging in...');

                $log.debug(response);
                $log.debug(message);

                toastr.error(message);

                blockUI.stop();
            });
    } // login

    var player = dataService.getLoggedInPlayer();

    if (player) {
        $location.path('/overview').replace();
        return;
    }

    $rootScope.menuItems = [];
    $rootScope.refreshButton = false;

    $scope.player = {
        name: '',
        password: ''
    };

    dataService.getUserName()
        .then(function (username) {
            if (username) {
                $scope.player.name = username;
            }

            return dataService.getPassword();
        }).then(function (password) {
            if (password) {
                $scope.player.password = password;
            }

            if ($scope.player.name && $scope.player.password) {
                return login($scope.player.name, $scope.player.password);
            }
        }).catch($log.debug)
        .then(blockUI.stop);

    $scope.login = login;
}); // LoginController
