'use strict';

/*jslint browser: true, nomen: true, stupid: true, todo: true */
/*global _, cordova, dirisApp, moment, utils */

dirisApp.factory('dataService', function dataService(
    $localStorage,
    $location,
    $log,
    $http,
    $q,
    authManager,
    jwtHelper,
    BACKEND_URL,
    CACHE_TIMEOUT,
    PIXABAY_KEY,
    UNSPLASH_KEY
) {
    var factory = {},
        matches = {},
        players = {},
        images = {},
        chats = {},
        token = null,
        loggedInPlayer = null,
        gcmRegistrationID = null,
        nextUpdate = null,
        secureStorage = new cordova.plugins.SecureStorage($log.debug, $log.error, 'diris');

    factory.logout = function logout() {
        factory.setToken(null);
        factory.setNextUpdate();
        matches = {};
        players = {};
        images = {};
        $localStorage.$reset();
        secureStorage.clear($log.debug, $log.debug);
    };

    factory.setNextUpdate = function setNextUpdate(nxt) {
        nextUpdate = nxt === '_renew' ? _.now() + CACHE_TIMEOUT : nxt || _.now() - 1;
        $localStorage.nextUpdate = nextUpdate;
        return nextUpdate;
    };

    factory.getNextUpdate = function getNextUpdate() {
        nextUpdate = nextUpdate || $localStorage.nextUpdate || _.now() - 1;
        $localStorage.nextUpdate = nextUpdate;
        return nextUpdate;
    };

    function getSecureStorage(key) {
        if (!secureStorage) {
            return $q.reject('no storage');
        }

        return $q(function (resolve, reject) {
            secureStorage.get(resolve, reject, key);
        });
    }

    function setSecureStorage(key, value) {
        if (!secureStorage) {
            return $q.reject('no storage');
        }

        return $q(function (resolve, reject) {
            secureStorage.set(resolve, reject, key, value);
        });
    }

    factory.setUserName = function setUserName(username) {
        return setSecureStorage('username', username);
    };

    factory.getUserName = function getUserName() {
        return getSecureStorage('username');
    };

    factory.setPassword = function setPassword(password) {
        if (utils.isBrowser()) {
            return $q.resolve(false);
        }

        return setSecureStorage('password', password);
    };

    factory.getPassword = function getPassword() {
        return getSecureStorage('password');
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

                if (token) {
                    factory.setUserName(username)
                        .then(function (response) {
                            $log.debug(response);
                            return factory.setPassword(password);
                        }).then($log.debug)
                        .catch($log.debug);
                }

                return token;
            }).catch(function (response) {
                $log.debug(response);
                factory.logout();
                throw response.data;
            });
    };

    factory.getTokenSync = function getTokenSync() {
        token = token || $localStorage.token;
        return (token && !jwtHelper.isTokenExpired(token)) ? token : undefined;
    };

    factory.resetPassword = function resetPassword(username, email) {
        return $http.post(BACKEND_URL + '/players/reset_password/',
                {username: username, email: email},
                {skipAuthorization: true});
    };

    factory.setGcmRegistrationID = function setGcmRegistrationID(gri) {
        gcmRegistrationID = gri || gcmRegistrationID;
    };

    factory.getLoggedInPlayer = function getLoggedInPlayer() {
        token = token || $localStorage.token;

        if (!token || !authManager.isAuthenticated()) {
            factory.setToken(null);
            return;
        }

        loggedInPlayer = loggedInPlayer || $localStorage.loggedInPlayer;

        if (!utils.isBrowser() && loggedInPlayer && gcmRegistrationID &&
                gcmRegistrationID !== loggedInPlayer.gcm_registration_id) {
            var gri = gcmRegistrationID;
            gcmRegistrationID = null;
            $log.debug('old GCM registration ID:', loggedInPlayer.gcm_registration_id);
            $log.debug('new GCM registration ID:', gri);
            factory.updatePlayer(loggedInPlayer.pk, {
                gcm_registration_id: gri
            })
                .then($log.debug)
                .catch($log.debug);
        }

        return loggedInPlayer;
    };

    function setMatch(match) {
        match = utils.processMatch(match, loggedInPlayer);
        $localStorage['match_' + match.pk] = match;
        matches[match.pk] = match;
    }

    factory.removeMatch = function removeMatch(matchPk) {
        delete $localStorage['match_' + matchPk];
        delete matches[matchPk];
    };

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

    factory.getMatches = function getMatches(forceRefresh, fallback, page) {
        if (!forceRefresh) {
            if (!_.size(matches)) {
                _.forEach($localStorage, function (match, key) {
                    if (_.startsWith(key, 'match_') && !matches[match.pk]) {
                        setMatch(match);
                    }
                });
            }

            return $q.resolve(matches);
        }

        factory.setNextUpdate('_renew');

        page = _.parseInt(page) || 1;

        return $http.get(BACKEND_URL + '/matches/?page=' + page)
            .then(function (response) {
                // TODO delete old matches from localStorage
                matches = page === 1 ? {} : matches;

                _.forEach(response.data.results, setMatch);

                var result = _.clone(matches);
                result._total = _.parseInt(response.data.count) || _.size(response.data.results);
                result._nextPage = response.data.next ? page + 1 : null;
                result._prevPage = response.data.previous ? page - 1 : null;

                return result;
            }).catch(function (response) {
                if (forceRefresh && fallback) {
                    // TODO add message
                    _.forEach($localStorage, function (match, key) {
                        if (_.startsWith(key, 'match_')) {
                            setMatch(match);
                        }
                    });
                    return matches;
                }

                throw new Error(response);
            });
    };

    factory.getMatch = function getMatch(mPk, forceRefresh, checkStatus) {
        if (!forceRefresh && matches[mPk]) {
            return $q.resolve(matches[mPk]);
        }

        if (!forceRefresh && $localStorage['match_' + mPk]) {
            setMatch($localStorage['match_' + mPk]);
            return $q.resolve(matches[mPk]);
        }

        return $http.get(BACKEND_URL + '/matches/' + mPk + (checkStatus ? '/check/' : '/'))
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
        player.avatar_url = utils.normalizeUrl(player.avatar_url, $location.protocol());
        $localStorage['player_' + player.pk] = player;
        players[player.pk] = player;

        if (player && loggedInPlayer && loggedInPlayer.pk === player.pk) {
            loggedInPlayer = _.merge(loggedInPlayer, player);
            $localStorage.loggedInPlayer = loggedInPlayer;
        }
    }

    factory.createPlayer = function createPlayer(newPlayer) {
        return $http.post(BACKEND_URL + '/players/',
            {user: newPlayer}, {skipAuthorization: true})
            .then(function (response) {
                var player = response.data;

                if (!player) {
                    throw response;
                }

                factory.setToken(player.token);

                setPlayer(player);

                return player;
            }).catch(function (response) {
                $log.debug('error');
                $log.debug(response);

                factory.logout();

                throw response.data;
            });
    };

    factory.updatePlayer = function updatePlayer(pPk, player) {
        return $http.patch(BACKEND_URL + '/players/' + pPk + '/', player)
            .then(function (response) {
                $log.debug("Successfully updated player", pPk);
                $log.debug(response);
                setPlayer(response.data);
                return player;
            }).catch(function (response) {
                $log.debug("Failed to updated player", pPk);
                $log.debug(response);

                throw new Error(response);
            });
    };

    factory.getPlayers = function getPlayers(forceRefresh, fallback, page) {
        if (!forceRefresh) {
            if (!_.size(players)) {
                _.forEach($localStorage, function (player, key) {
                    if (_.startsWith(key, 'player_') && !players[player.pk]) {
                        setPlayer(player);
                    }
                });
            }

            return $q.resolve(players);
        }

        factory.setNextUpdate('_renew');

        page = _.parseInt(page) || 1;

        return $http.get(BACKEND_URL + '/players/?page=' + page)
            .then(function (response) {
                // TODO delete old player data from localStorage
                players = page === 1 ? {} : players;

                _.forEach(response.data.results, setPlayer);

                var result = _.clone(players);
                result._total = _.parseInt(response.data.count) || _.size(response.data.results);
                result._nextPage = response.data.next ? page + 1 : null;
                result._prevPage = response.data.previous ? page - 1 : null;

                return result;
            }).catch(function (response) {
                if (forceRefresh && fallback) {
                    // TODO add message
                    _.forEach($localStorage, function (player, key) {
                        if (_.startsWith(key, 'player_')) {
                            players[player.pk] = player;
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
        image.url = utils.normalizeUrl(image.url, $location.protocol());
        $localStorage['image_' + image.pk] = image;
        images[image.pk] = image;
    }

    factory.getImages = function getImages(mPk, forceRefresh, fallback) {
        if (!mPk) {
            return $q.reject('match is required');
        }

        if (forceRefresh) {
            return $http.get(BACKEND_URL + '/matches/' + mPk + '/images/')
                .then(function (response) {
                    _.forEach(response.data, function (image) {
                        setImage(image);
                    });
                    return response.data;
                }).catch(function (response) {
                    $log.error('There has been an error', response);

                    if (fallback) {
                        return factory.getImages(mPk, false, false);
                    }

                    throw response;
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

    factory.queryImages = function queryImages(query) {
        return $q.all([
            $http.get('https://pixabay.com/api/?key=' + PIXABAY_KEY + '&per_page=20&q=' +
                    encodeURIComponent(query))
                .then(function (response) {
                    return _.map(response.data.hits, function (image) {
                        return {url: _.replace(image.webformatURL, '_640.', '_960.')};
                    });
                }),
            $http.get('https://api.unsplash.com/search/photos?client_id=' + UNSPLASH_KEY + '&per_page=20&query=' +
                    encodeURIComponent(query))
                .then(function (response) {
                    return _.map(response.data.results, function (image) {
                        return {url: image.urls.regular};
                    });
                })
        ]).then(function (images) {
            return _(images).flatten().shuffle().value();
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

    factory.setChatMessages = function setChatMessages(mPk, newMessages) {
        chats[mPk] = _(_.get(chats, mPk, []))
            .concat(newMessages)
            .map(function (message) {
                message.timestamp = moment(message.timestamp).startOf('second');
                return message;
            })
            .sortBy(['timestamp'])
            .filter(function (value, index, coll) {
                var prev = coll[index - 1];
                return (index === 0 ||
                    value.player !== prev.player ||
                    value.text !== prev.text ||
                    value.timestamp.toString() !== prev.timestamp.toString());
            }).value();
    };

    factory.getChat = function getChat(mPk, forceRefresh, seq) {
        if (!forceRefresh) {
            return $q.resolve(_.get(chats, mPk, []));
        }

        var url = BACKEND_URL + '/matches/' + mPk + '/chat/',
            seqNum = _.parseInt(seq);

        if (!_.isNaN(seqNum)) {
            url += '?seq=' + seqNum;
        }

        return $http.get(url).then(function (response) {
            var messageGroup = response.data;

            if (!messageGroup) {
                messageGroup = {
                    sequence: seqNum,
                    messages: []
                };
            }

            factory.setChatMessages(mPk, messageGroup.messages);

            // TODO make 10 a parameter
            if (_.size(messageGroup.messages) < 10 && messageGroup.sequence > 0) {
                return factory.getChat(mPk, true, messageGroup.sequence - 1);
            }

            return chats[mPk];
        });
    };

    factory.sendChat = function sendChat(mPk, text) {
        return $http.post(BACKEND_URL + '/matches/' + mPk + '/chat/', {text: text})
            .then(function (response) {
                var messageGroup = response.data;

                if (!messageGroup) {
                    throw new Error(response);
                }

                factory.setChatMessages(mPk, messageGroup.messages);

                return chats[mPk];
            });
    };

    factory.setChatViewed = function setChatViewed(mPk, date) {
        $localStorage['chat_' + mPk] = date || moment();
    };

    factory.getChatViewed = function getChatViewed(mPk) {
        return moment(_.get($localStorage, 'chat_' + mPk));
    };

    factory.getChatNumNew = function getChatNumNew(mPk, forceRefresh) {
        return factory.getChat(mPk, forceRefresh)
            .then(function (messages) {
                if (_.isEmpty(messages)) {
                    return 0;
                }

                var lastViewed = factory.getChatViewed(mPk);

                return _(messages).filter(function (message) {
                    return message.timestamp.isAfter(lastViewed);
                }).size();
            });
    };

    return factory;
});
