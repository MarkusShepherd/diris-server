'use strict';

/*jslint browser: true, stupid: true, todo: true */
/*global angular, PushNotification */

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
    .constant('MINIMUM_STORY_LENGTH', 3)
    .constant('MINIMUM_PLAYER', 4)
    .constant('MAXIMUM_PLAYER', 10)
    .constant('STANDARD_TIMEOUT', 60 * 60 * 36)
    .constant('GCM_SENDER_ID', 696693451234)
    .constant('DEVELOPER_MODE', false);

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

    $logProvider.debugEnabled(DEVELOPER_MODE);

    blockUIConfig.autoBlock = false;

    // TODO replace with _ function
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

dirisApp.run(function ($log, authManager, toastr, dataService, GCM_SENDER_ID) {
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
});
