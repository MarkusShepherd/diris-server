'use strict';

/*jslint browser: true, nomen: true */
/*global _, dirisApp, utils */

dirisApp.controller('VoteImageController', function VoteImageController(
    $location,
    $log,
    $q,
    $rootScope,
    $routeParams,
    $scope,
    blockUI,
    toastr,
    dataService
) {
    var player = dataService.getLoggedInPlayer(),
        mPk = $routeParams.mPk,
        rNo = $routeParams.rNo,
        matchPromise,
        imagePromise;

    if (!player) {
        $location.search('dest', $location.path()).path('/login');
        return;
    }

    if (!blockUI.state().blocking) {
        blockUI.start();
    }

    $scope.currentPlayer = player;
    $scope.mPk = mPk;
    $scope.rNo = rNo;

    $rootScope.menuItems = [{
        link: '#/overview',
        label: 'Overview',
        glyphicon: 'home'
    }, {
        link: '#/match/' + mPk,
        label: 'Match',
        glyphicon: 'knight'
    }, {
        link: '#/chat/' + mPk,
        label: 'Chat',
        glyphicon: 'send'
    }];
    $rootScope.refreshButton = false;

    matchPromise = dataService.getMatch(mPk)
        .then(function (match) {
            var round = match.rounds[rNo - 1],
                action = utils.roundAction(round);

            if (action !== 'vote') {
                $location.path('/' + action + '/' + mPk + '/' + rNo).replace();
                return;
            }

            $scope.match = match;
            $scope.round = round;

            return $q.all(_.map(match.players, function (pk) {
                return dataService.getPlayer(pk, false);
            }));
        }).then(function (players) {
            $scope.players = {};
            _.forEach(players || [], function (player) {
                $scope.players[player.pk.toString()] = player;
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    imagePromise = dataService.getImages(mPk)
        .then(function (images) {
            $scope.images = {};
            _.forEach(images || [], function (img) {
                $scope.images[img.pk.toString()] = img;
            });
        }).catch(function (response) {
            $log.debug('error');
            $log.debug(response);
            toastr.error("There was an error fetching the data - please try again later...");
        });

    $q.all([matchPromise, imagePromise]).then(blockUI.stop);

    $scope.selectImage = function selectImage(image) {
        if (image.pk !== $scope.round.playerDetails.image) {
            $scope.selectedImage = image;
        }
    };

    $scope.submitVote = function submitVote() {
        if (!blockUI.state().blocking) {
            blockUI.start();
        }

        dataService.submitVote(mPk, rNo, $scope.selectedImage.pk)
            .then(function (match) {
                var round = match.rounds[rNo - 1],
                    votedFor = _.get(round, 'details.' + player.pk + '.vote_player');

                if (votedFor === round.storyteller) {
                    toastr.success('Congratulations! You selected the right image!', 'Good choice');
                } else if (votedFor) {
                    toastr.error("That wasn't the storyteller's image – " +
                                 _.get($scope, 'players.' + votedFor + '.user.username') +
                                 ' deceived you...', 'No luck');
                }

                $location.path('/review/' + mPk + '/' + rNo).replace();
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);
                blockUI.stop();
                toastr.error("There was an error");
            });
    };
});
