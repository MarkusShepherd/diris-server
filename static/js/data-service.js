'use strict';

dirisApp.factory('dataService', function dataService(
    $localStorage,
    $log,
    $http,
    $q,
    authManager,
    jwtHelper,
    BACKEND_URL
) {
    var factory = {},
        matches = {},
        players = {},
        images = {},
        token = null,
        loggedInPlayer = null;
        // gcmRegistrationID = null;

    factory.logout = function logout() {
        factory.setToken(null);
        matches = {};
        players = {};
        images = {};
        $localStorage.$reset();
    };

    factory.setToken = function setToken(newToken) {
        if (newToken && !jwtHelper.isTokenExpired(newToken)) {
            token = newToken;
            loggedInPlayer = jwtHelper.decodeToken(newToken);
            authManager.authenticate();
        } else {
            token = null;
            loggedInPlayer = null;
            authManager.unauthenticate();
        }

        $localStorage.token = token;
        $localStorage.loggedInPlayer = loggedInPlayer;
    };

    factory.getToken = function getToken(username, password) {
        token = token || $localStorage.token;

        if (token && !jwtHelper.isTokenExpired(token)) {
            factory.setToken(token);
            return $q.resolve(token);
        }

        return $http.post(BACKEND_URL + '/jwt',
            {username: username, password: password},
            {skipAuthorization: true})
            .then(function (response) {
                factory.setToken(response.data.token);
                return token;
            }).catch(function (response) {
                factory.logout();
                throw new Error(response);
            });
    };

    factory.getTokenSync = function getTokenSync() {
        token = token || $localStorage.token;
        return (token && !jwtHelper.isTokenExpired(token)) ? token : undefined;
    };

    factory.registerPlayer = function registerPlayer(newPlayer) {
        return $http.post(BACKEND_URL + '/players/',
            {user: newPlayer}, {skipAuthorization: true})
            .then(function (response) {
                var player = response.data;

                if (!player) {
                    throw new Error(response);
                }

                factory.setToken(player.token);

                return player;
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);

                factory.logout();

                throw new Error(response);
            });
    };

    factory.getLoggedInPlayer = function getLoggedInPlayer() {
        token = token || $localStorage.token;

        if (!token || !authManager.isAuthenticated()) {
            factory.setToken(null);
            return;
        }

        loggedInPlayer = loggedInPlayer || $localStorage.loggedInPlayer;
        return loggedInPlayer;
    };

    function setMatch(match) {
        match = processMatch(match, loggedInPlayer);
        $localStorage['match_' + match.pk] = match;
        matches[match.pk] = match;
    }

    factory.createMatch = function createMatch(playerPks, totalRounds, timeout) {
        var player = factory.getLoggedInPlayer(),
            options = {
                players: playerPks,
                inviting_player: player.pk
            };

        if (_.isFinite(totalRounds)) {
            options.total_rounds = totalRounds;
        }

        if (_.isFinite(timeout)) {
            options.timeout = timeout;
        }

        return $http.post(BACKEND_URL + '/matches/', options)
            .then(function (response) {
                var match = response.data;

                if (!match) {
                    throw new Error(response);
                }

                setMatch(match);

                return match;
            });
    };

    factory.getMatches = function getMatches(forceRefresh, fallback) {
        if (!forceRefresh) {
            return $q.resolve(matches);
        }

        return $http.get(BACKEND_URL + '/matches/')
            .then(function (response) {
                $log.debug('Matches from server:', response.data.results);
                matches = {};
                _.forEach(response.data.results, setMatch);
                return matches;
            }).catch(function (response) {
                if (forceRefresh && fallback) {
                    // TODO add message
                    _.forEach($localStorage, function (match, key) {
                        if (key.substr(0, 6) === 'match_') {
                            setMatch(match);
                        }
                    });
                    return matches;
                }

                throw new Error(response);
            });
    };

    factory.getMatch = function getMatch(mPk, forceRefresh) {
        if (!forceRefresh && matches[mPk]) {
            return $q.resolve(matches[mPk]);
        }

        if (!forceRefresh && $localStorage['match_' + mPk]) {
            setMatch($localStorage['match_' + mPk]);
            return $q.resolve(matches[mPk]);
        }

        return $http.get(BACKEND_URL + '/matches/' + mPk + '/')
            .then(function (response) {
                $log.debug('Match from server:', response.data);
                setMatch(response.data);
                return matches[mPk];
            });
    };

    factory.respondToInvitation = function respondToInvitation(mPk, accept) {
        var action = accept ? '/accept/' : '/decline/';
        return $http.post(BACKEND_URL + '/matches/' + mPk + action, '')
            .then(function (response) {
                var match = response.data;

                if (!match) {
                    throw new Error(response);
                }

                setMatch(match);

                return match;
            });
    };

    function setPlayer(player) {
        $localStorage['player_' + player.pk] = player;
        players[player.pk] = player;
    }

    factory.getPlayers = function getPlayers(forceRefresh, fallback) {
        if (!forceRefresh) {
            return $q.resolve(players);
        }

        return $http.get(BACKEND_URL + '/players/')
            .then(function (response) {
                players = {};
                _.forEach(response.data.results, function (player) {
                    setPlayer(player);
                });
                return players;
            }).catch(function (response) {
                if (forceRefresh && fallback) {
                    // TODO add message
                    _.forEach($localStorage, function (player, key) {
                        if (key.substr(0, 7) === 'player_') {
                            players[key.substr(7)] = player;
                        }
                    });
                    return players;
                }

                throw new Error(response);
            });
    };

    factory.getPlayer = function getPlayer(pPk, forceRefresh) {
        if (!forceRefresh && players[pPk]) {
            return $q.resolve(players[pPk]);
        }

        if (!forceRefresh && $localStorage['player_' + pPk]) {
            players[pPk] = $localStorage['player_' + pPk];
            return $q.resolve(players[pPk]);
        }

        return $http.get(BACKEND_URL + '/players/' + pPk + '/')
            .then(function (response) {
                setPlayer(response.data);
                return players[pPk];
            });
    };

    function setImage(image) {
        // TODO http or https?
        if (_.startsWith(image.url, '//')) {
            image.url = 'http:' + image.url;
        }
        $localStorage['image_' + image.pk] = image;
        images[image.pk] = image;
    }

    factory.getImages = function getImages(mPk, forceRefresh, fallback) {
        if (mPk) {
            if (forceRefresh) {
                return $http.get(BACKEND_URL + '/matches/' + mPk + '/images/')
                    .then(function (response) {
                        _.forEach(response.data, function (image) {
                            setImage(image);
                        });
                        return response.data;
                    }).catch(function (response) {
                        $log.debug('There has been an error', response);
                        if (fallback) {
                            return factory.getImages(mPk, false, false);
                        }

                        throw new Error(response);
                    });
            }

            return factory.getMatch(mPk)
                .then(function (match) {
                    var promises = _.flatMap(match.rounds || [], function (round) {
                        return _.map(round.images || [], factory.getImage);
                    });
                    return $q.all(promises);
                }).catch(function (response) {
                    $log.debug('There has been an error', response);
                    return $q.resolve(images);
                });
        }

        if (!forceRefresh) {
            return $q.resolve(images);
        }

        return $http.get(BACKEND_URL + '/images/')
            .then(function (response) {
                images = {};
                _.forEach(response.data.results, setImage);
                return images;
            }).catch(function (response) {
                if (forceRefresh && fallback) {
                    // TODO add message
                    _.forEach($localStorage, function (image, key) {
                        if (key.substr(0, 6) === 'image_') {
                            images[key.substr(6)] = image;
                        }
                    });
                    return images;
                }

                throw new Error(response);
            });
    };

    factory.getRandomImages = function getRandomImages(size) {
        size = _.toInteger(size);
        return $http.get(BACKEND_URL + '/images/random/', {params: {size: size}})
            .then(function (response) {
                _.forEach(response.data, setImage);
                return response.data;
            });
    };

    factory.getImage = function getImage(iPk, forceRefresh) {
        if (!forceRefresh && images[iPk]) {
            return $q.resolve(images[iPk]);
        }

        if (!forceRefresh && $localStorage['image_' + iPk]) {
            images[iPk] = $localStorage['image_' + iPk];
            return $q.resolve(images[iPk]);
        }

        return $http.get(BACKEND_URL + '/images/' + iPk + '/')
            .then(function (response) {
                setImage(response.data);
                return images[iPk];
            });
    };

    factory.submitImage = function submitImage(mPk, rNo, image, story) {
        return $http.post(BACKEND_URL + '/matches/' + mPk + '/' + rNo + '/image/filename.jpeg', image, {
            headers: {'Content-Type': 'image/jpeg'},
            params: {story: story},
        }).then(function (response) {
            var match = response.data;

            if (!match) {
                throw new Error(response);
            }

            setMatch(match);

            return match;
        });
    };

    factory.submitVote = function submitVote(mPk, rNo, iPk) {
        return $http.post(BACKEND_URL + '/matches/' + mPk + '/' + rNo + '/vote/' + iPk, '')
            .then(function (response) {
                var match = response.data;

                if (!match) {
                    throw new Error(response);
                }

                setMatch(match);

                return match;
            });
    };

    // TODO
    // factory.setGcmRegistrationId = function(gri) {
    //  gcmRegistrationID = gri;
    // };

    // TODO
    // factory.updatePlayer = function(pId, player) {
    //  $http.post(BACKEND_URL + '/player/update/' + pId, player)
    //  .then(function(response) {
    //      $log.debug("Successfully updated player " + pId);
    //      $log.debug(response);
    //  })
    //  .catch(function(response) {
    //      $log.debug("Failed to updated player " + pId);
    //      $log.debug(response);
    //  });
    // };

    return factory;
});
