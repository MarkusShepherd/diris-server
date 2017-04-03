'use strict';

var testUrl = 'http://localhost:8000';
var liveUrl = 'https://diris-app.appspot.com';

var dirisApp = angular.module('dirisApp', [
    'angular-jwt',
    'blockUI',
    'ngAnimate',
    'ngRoute',
    'ngStorage',
    'toastr'
]);

dirisApp.constant('BACKEND_URL', liveUrl);

dirisApp.config(function (
    $httpProvider,
    $routeProvider,
    $localStorageProvider,
    $locationProvider,
    $logProvider,
    blockUIConfig,
    jwtOptionsProvider,
    toastrConfig
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
    }).when('/overview', {
        templateUrl: 'partials/overview.html',
        controller: 'OverviewController',
        requiresLogin: true
    }).when('/overview/:action', {
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
    }).when('/match/:mPk/:action', {
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

    $logProvider.debugEnabled(false);

    blockUIConfig.autoBlock = false;

    angular.extend(toastrConfig, {
        autoDismiss: false,
        newestOnTop: false,
        positionClass: 'toast-bottom-right',
        preventDuplicates: false,
        preventOpenDuplicates: true,
        extendedTimeOut: 1000,
        timeOut: 10000
        // TODO force refresh on click
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

dirisApp.run(function ($log, authManager, toastr, dataService) {
    authManager.checkAuthOnRefresh();

    if (isBrowser()) {
        $log.debug('No notifications on browser');
    } else {
        var push = PushNotification.init({
            android: {
                senderID: 879361060795
            },
            ios: {
                alert: true,
                badge: true,
                sound: true
            },
            windows: {}
        });

        push.on('registration', function (data) {
            $log.debug("Registered push");
            $log.debug(data);
            $log.debug(data.registrationId);

            var player = dataService.getLoggedInPlayer();
            if (player && player.pk) {
                dataService.updatePlayer(player.pk, {
                    gcmRegistrationID: data.registrationId
                });
            } else {
                dataService.setGcmRegistrationId(data.registrationId);
            }
        });

        push.on('notification', function (data) {
            $log.debug("Received notification");
            $log.debug(data);
            $log.debug(data.message);
            $log.debug(data.title);
            $log.debug(data.count);
            $log.debug(data.sound);
            $log.debug(data.image);
            $log.debug(data.additionalData);
            toastr.info(data.message, data.title);
        });

        push.on('error', function (e) {
            $log.debug("Error in notifications");
            $log.debug(e);
            $log.debug(e.message);
            toastr.error(e.message);
        });
    }
});
