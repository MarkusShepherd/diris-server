'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp, utils */

dirisApp.controller('ChatController', function ChatController(
    $anchorScroll,
    $interval,
    $location,
    $log,
    $q,
    $rootScope,
    $routeParams,
    $scope,
    $timeout,
    blockUI,
    toastr,
    dataService
) {
    var player = dataService.getLoggedInPlayer(),
        mPk = $routeParams.mPk,
        matchPromise,
        chatPromise,
        intervalPromise;

    if (!player) {
        $location.search('dest', $location.path()).path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.currentPlayer = player;

    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }, {
        link: '#/match/' + mPk,
        label: 'Match',
        glyphicon: 'knight'
    }];
    $rootScope.refreshButton = true;

    matchPromise = dataService.getMatch(mPk)
        .then(function (match) {
            $log.debug('Match:', match);
            $scope.match = match;
            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.playersArray = players;
            $scope.players = {};
            _.forEach(players, function (player) {
                $scope.players[player.pk.toString()] = player;
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the data - please try again later...');
        });

    chatPromise = dataService.getChat(mPk, true)
        .then(function (messages) {
            $scope.messages = messages;
            dataService.setChatViewed(mPk);
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error('There was an error fetching the data - please try again later...');
        });

    $q.all([matchPromise, chatPromise])
        .then(blockUI.stop)
        .then(function () {
            return $timeout(function () {
                $anchorScroll('submit');
            }, 100);
        }).then(function () {
            intervalPromise = $interval(function () {
                dataService.getChat(mPk, false).then(function (messages) {
                    $scope.messages = messages;
                    dataService.setChatViewed(mPk);
                });
            }, 1000);
            return intervalPromise;
        });

    $scope.hasOnlyEmojis = utils.hasOnlyEmojis;

    $scope.sendMessage = function sendMessage() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        dataService.sendChat(mPk, $scope.text)
            .then(function (messages) {
                $log.debug(messages);
                $scope.text = null;
                $scope.messages = messages;
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);
                toastr.error('There was an error sending the message - please try again...');
            }).then(blockUI.stop)
            .then(function () {
                return $timeout(function () {
                    $anchorScroll('submit');
                    dataService.setChatViewed(mPk);
                }, 100);
            });
    };

    $scope.$on('$destroy', function () {
        if (!_.isNil(intervalPromise)) {
            $interval.cancel(intervalPromise);
        }
    });
}); // MatchController
