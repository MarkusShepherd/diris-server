'use strict';

/*jslint browser: true, nomen: true, stupid: true, todo: true */
/*global _, angular, PushNotification */

var testUrl = 'http://localhost:8000',
    stagingUrl = 'https://0-2-1-dot-diris-app.appspot.com',
    liveUrl = 'https://diris-app.appspot.com';

var dirisApp = angular.module('dirisApp', [
    'angular-jwt',
    'blockUI',
    'ngAnimate',
    'ngRoute',
    'ngStorage',
    'toastr'
]);

dirisApp.constant('BACKEND_URL', liveUrl)
    .constant('DEVELOPER_MODE', false)
    .constant('MINIMUM_STORY_LENGTH', 3)
    .constant('MINIMUM_PLAYER', 4)
    .constant('MAXIMUM_PLAYER', 10)
    .constant('STANDARD_TIMEOUT', 60 * 60 * 36)
    .constant('CACHE_TIMEOUT', 60 * 60 * 1000)
    .constant('GCM_SENDER_ID', 696693451234)
    .constant('ANDROID_APP_LINK', 'https://diris-app.appspot.com/diris.apk')
    .constant('CREATOR_NAME', 'Markus Shepherd')
    .constant('CREATOR_LINK', 'http://www.riemannhypothesis.info/')
    .constant('FEEDBACK_EMAIL', 'markus.r.shepherd@gmail.com')
    .constant('FEEDBACK_LINK', 'https://bitbucket.org/MarkusShepherd/diris-app/issues/new');

dirisApp.config(function (
    $httpProvider,
    $routeProvider,
    $localStorageProvider,
    $locationProvider,
    $logProvider,
    blockUIConfig,
    jwtOptionsProvider,
    toastrConfig,
    DEVELOPER_MODE
) {
    jwtOptionsProvider.config({
        authPrefix: 'JWT ',
        unauthenticatedRedirectPath: '/login',
        whiteListedDomains: ['diris-app.appspot.com', 'localhost'],
        tokenGetter: ['dataService', function (dataService) {
            return dataService.getTokenSync();
        }]
    });

    $httpProvider.interceptors.push('jwtInterceptor');

    $routeProvider.when('/login', {
        templateUrl: 'partials/login.html',
        controller: 'LoginController'
    }).when('/register', {
        templateUrl: 'partials/registration.html',
        controller: 'RegistrationController'
    }).when('/forgot', {
        templateUrl: 'partials/forgot-password.html',
        controller: 'ForgotPasswordController'
    }).when('/overview', {
        templateUrl: 'partials/overview.html',
        controller: 'OverviewController',
        requiresLogin: true
    }).when('/newmatch', {
        templateUrl: 'partials/new-match.html',
        controller: 'NewMatchController',
        requiresLogin: true
    }).when('/accept/:mPk', {
        templateUrl: 'partials/accept.html',
        controller: 'AcceptController',
        requiresLogin: true
    }).when('/match/:mPk', {
        templateUrl: 'partials/match.html',
        controller: 'MatchController',
        requiresLogin: true
    }).when('/image/:mPk/:rNo', {
        templateUrl: 'partials/submit-image.html',
        controller: 'SubmitImageController',
        requiresLogin: true
    }).when('/vote/:mPk/:rNo', {
        templateUrl: 'partials/vote-image.html',
        controller: 'VoteImageController',
        requiresLogin: true
    }).when('/review/:mPk/:rNo', {
        templateUrl: 'partials/review-round.html',
        controller: 'ReviewRoundController',
        requiresLogin: true
    }).when('/profile', {
        templateUrl: 'partials/profile.html',
        controller: 'ProfileController',
        requiresLogin: true
    }).when('/profile/:pPk', {
        templateUrl: 'partials/profile.html',
        controller: 'ProfileController',
        requiresLogin: true
    }).when('/profile/:pPk/:action', {
        templateUrl: 'partials/profile.html',
        controller: 'ProfileController',
        requiresLogin: true
    }).otherwise({
        redirectTo: '/login'
    });

    $locationProvider.hashPrefix('');

    $localStorageProvider.setKeyPrefix('dirisApp_');

    $logProvider.debugEnabled(DEVELOPER_MODE);

    blockUIConfig.autoBlock = false;

    _.assign(toastrConfig, {
        autoDismiss: false,
        newestOnTop: false,
        positionClass: 'toast-bottom-right',
        preventDuplicates: false,
        preventOpenDuplicates: true,
        extendedTimeOut: 1000,
        timeOut: 10000
    });
});

dirisApp.directive('playerIcon', function () {
    return {
        restrict: 'E',
        templateUrl: 'partials/widgets/player-icon.html',
        scope: {
            player: '=',
            classIcon: '@',
            classImg: '@',
            classBtn: '@'
        }
    };
});

dirisApp.run(function (
    $location,
    $log,
    $q,
    $route,
    authManager,
    toastr,
    dataService,
    GCM_SENDER_ID
) {
    authManager.checkAuthOnRefresh();

    var push = PushNotification.init({
        android: {
            senderID: GCM_SENDER_ID
        },
        browser: {},
        ios: {
            alert: true,
            badge: true,
            sound: true,
            vibration: true
        },
        windows: {}
    });

    push.on('registration', function (data) {
        $log.debug('registration event:', data.registrationId);
        dataService.setGcmRegistrationID(data.registrationId);
    });

    push.on('notification', function (data) {
        var promise = $q.resolve(),
            options = {},
            path = null;

        $log.debug('received notification:', data);
        $log.debug(data.additionalData.match_pk);

        if (data.additionalData.match_pk === '_new') {
            path = '/overview';
            promise = dataService.getMatches(true, true);

            options.onTap = function () {
                $location.path(path);
            };

            if (!data.additionalData.foreground || data.additionalData.coldstart) {
                $location.path(path);
            }
        } else if (data.additionalData.match_pk) {
            path = '/match/' + data.additionalData.match_pk;
            promise = dataService.getMatch(data.additionalData.match_pk, true);

            options.onTap = function () {
                $location.path(path);
            };

            if (!data.additionalData.foreground || data.additionalData.coldstart) {
                $location.path(path);
            }
        }

        promise.then(function () {
            if (_.startsWith($location.path(), '/overview') ||
                    _.startsWith($location.path(), '/match') ||
                    _.startsWith($location.path(), '/review')) {
                $route.reload();
            }
        }).catch($log.debug)
            .then(function () {
                toastr.info(data.message, data.title, options);
            });
    });

    push.on('error', function (e) {
        $log.debug('error in notifications:', e);
        $log.debug(e.message);
        toastr.error(e.message);
    });
});
