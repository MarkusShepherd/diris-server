'use strict';

/*jslint browser: true, nomen: true */
/*global angular, $, _, moment, device, navigator, utils, dirisApp */

dirisApp.controller('NavigationController', function NavigationController(
    $location,
    $rootScope,
    $route,
    $scope,
    dataService
) {
    $scope.$watch(dataService.getLoggedInPlayer, function (player) {
        $scope.currentPlayer = player;
    });

    $scope.logout = function logout() {
        dataService.logout();
        $location.path('/login');
    };

    $scope.refresh = function refresh() {
        if ($rootScope.refreshReload) {
            $route.reload();
        } else if ($rootScope.refreshPath) {
            $location.path($rootScope.refreshPath).replace();
        }
    };
});
