'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp */

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
                var message = _.upperFirst(response.data.detail || response.data.message ||
                                           response.data.toString() || 'There was an error...');

                $log.debug(response);
                $log.debug(message);

                toastr.error(message);

                blockUI.stop();
            });
    }; // reset
}); // ForgotPasswordController
