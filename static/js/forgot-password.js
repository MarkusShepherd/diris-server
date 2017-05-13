'use strict';

/*jslint browser: true */
/*global dirisApp */

dirisApp.controller('ForgotPasswordController', function ForgotPasswordController(
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

    $scope.reset = function reset() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        dataService.resetPassword($scope.username, $scope.email)
            .then(function () {
                toastr.success('You should receive an email with your new password', 'Check your emails');
                $location.path('/login').replace();
            }).catch(function (response) {
                $log.debug(response);
                $scope.message = response.message || "There was an error...";
                blockUI.stop();
            })
    }; // reset
}); // ForgotPasswordController
