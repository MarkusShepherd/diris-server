'use strict';

/*jslint browser: true */
/*global dirisApp */

dirisApp.controller('NavigationController', function NavigationController(
    $location,
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
        dataService.setNextUpdate();
        $route.reload();
    };
});
