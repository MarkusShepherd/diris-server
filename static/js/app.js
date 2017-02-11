var testUrl = 'http://localhost:8181';
var liveUrl = 'http://dixit-app.appspot.com';
var devUrl  = 'https://0-1-0-dot-dixit-app.appspot.com/';

var dixitApp = angular.module('dixitApp', ['angular-jwt', 'auth0', 'blockUI', 'ngAnimate', 'ngRoute', 'ngStorage', 'toastr']);

dixitApp.constant('BACKEND_URL', liveUrl);

dixitApp.config(function(authProvider, jwtInterceptorProvider, $httpProvider, $routeProvider,
	$localStorageProvider, $logProvider, blockUIConfig, toastrConfig) {
	authProvider.init({
		domain: 'dixit.auth0.com',
		clientID: 'SyQYBfqUOcxOgrXHjTUMKJGfJFPwLuBZ',
		loginUrl: '/login'
	});

	jwtInterceptorProvider.tokenGetter = ['$localStorage', function($localStorage) {
		return $localStorage.token;
	}];

	$httpProvider.interceptors.push('jwtInterceptor');

	$routeProvider.when('/login', {
		templateUrl : 'partials/login.html',
		controller : 'LoginController'
	}).when('/overview', {
		templateUrl : 'partials/overview.html',
		controller : 'OverviewController',
		requiresLogin: true
	}).when('/overview/:action', {
		templateUrl : 'partials/overview.html',
		controller : 'OverviewController',
		requiresLogin: true
	}).when('/newmatch', {
		templateUrl : 'partials/new-match.html',
		controller : 'NewMatchController',
		requiresLogin: true
	}).when('/accept/:mId', {
		templateUrl : 'partials/accept.html',
		controller : 'AcceptController',
		requiresLogin: true
	}).when('/match/:mId', {
		templateUrl : 'partials/match.html',
		controller : 'MatchController',
		requiresLogin: true
	}).when('/match/:mId/:action', {
		templateUrl : 'partials/match.html',
		controller : 'MatchController',
		requiresLogin: true
	}).when('/image/:mId/:rNo', {
		templateUrl : 'partials/submit-image.html',
		controller : 'SubmitImageController',
		requiresLogin: true
	}).when('/vote/:mId/:rNo', {
		templateUrl : 'partials/vote-image.html',
		controller : 'VoteImageController',
		requiresLogin: true
	}).when('/review/:mId/:rNo', {
		templateUrl : 'partials/review-round.html',
		controller : 'ReviewRoundController',
		requiresLogin: true
	}).when('/profile', {
		templateUrl : 'partials/profile.html',
		controller : 'ProfileController',
		requiresLogin: true
	}).when('/profile/:pId', {
		templateUrl : 'partials/profile.html',
		controller : 'ProfileController',
		requiresLogin: true
	}).when('/profile/:pId/:action', {
		templateUrl : 'partials/profile.html',
		controller : 'ProfileController',
		requiresLogin: true
	}).otherwise({
		redirectTo : '/login'
	});

	$localStorageProvider.setKeyPrefix('dixitApp_');

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

dixitApp.run(function($localStorage, $log, $rootScope, auth, dataService, toastr) {
	auth.hookEvents();

	$rootScope.$on('$locationChangeStart', function() {
		if (!auth.isAuthenticated) {
			var token = $localStorage.token;
			if (token)
				auth.authenticate($localStorage.profile, token);
		}
	});

	if (isBrowser())
		$log.debug('No notifications on browser');
	else {
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

		push.on('registration', function(data) {
			$log.debug("Registered push");
			$log.debug(data);
			$log.debug(data.registrationId);
			
			var player = dataService.getLoggedInPlayer();
			if (player && player.key && player.key.id)
				dataService.updatePlayer(player.key.id, {
    				gcmRegistrationID: data.registrationId
    			});
			else
				dataService.setGcmRegistrationId(data.registrationId);
		});

		push.on('notification', function(data) {
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

		push.on('error', function(e) {
			$log.debug("Error in notifications");
			$log.debug(e);
			$log.debug(e.message);
			toastr.error(e.message);
		});
	}
});
