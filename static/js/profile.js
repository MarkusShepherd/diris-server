'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp, utils */

dirisApp.controller('ProfileController', function ProfileController(
    $location,
    $log,
    $rootScope,
    $routeParams,
    $scope,
    blockUI,
    toastr,
    dataService
) {
    var loggedInPlayer = dataService.getLoggedInPlayer(),
        pPk = _.parseInt($routeParams.pPk),
        action = $routeParams.action,
        ownProfile = false;

    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }];
    $rootScope.refreshButton = false;

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    pPk = pPk || loggedInPlayer.pk;
    ownProfile = !!(loggedInPlayer && pPk === loggedInPlayer.pk);
    action = ownProfile ? action || 'edit' : 'view';

    $scope.edit = action === 'edit';
    $scope.ownProfile = ownProfile;
    $scope.uPlayer = {
        user: {}
    };

    dataService.getPlayer(pPk)
        .then(function (player) {
            $scope.player = player;

            $scope.uPlayer.user.username = player.user.username || loggedInPlayer.username;
            $scope.uPlayer.user.email = player.user.email || loggedInPlayer.email;
            $scope.uPlayer.user.first_name = player.user.first_name || loggedInPlayer.first_name;
            $scope.uPlayer.user.last_name = player.user.last_name || loggedInPlayer.last_name;
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
        }).then(blockUI.stop);

    $scope.setEdit = function setEdit(edit) {
        edit = !!(ownProfile && edit);
        action = edit ? 'edit' : 'view';
        $scope.edit = edit;
    };

    $scope.update = function update() {
        var player = utils.removeEmpty($scope.uPlayer);

        if (player.user.password && player.user.password !== player.user.repeat_password) {
            toastr.error("Passwords don't match");
            return;
        }

        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        dataService.updatePlayer(pPk, player)
            .then(function () {
                toastr.success('Player data updated');
                $location.path('/overview');
            }).catch(function (response) {
                $log.debug(response);
                toastr.error(response.details || response.message ||
                             response.toString() || 'There was an error...');
                blockUI.stop();
            });
    }; // update
}); // ProfileController
