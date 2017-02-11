dixitApp.controller('LoginController', 
function($http, $localStorage, $location, $log, $rootScope, $scope, $timeout, auth, blockUI, toastr, dataService, BACKEND_URL) {

	$rootScope.menuItems = [];
	$rootScope.refreshPath = null;
	$rootScope.refreshReload = false;

	if (auth.isAuthenticated)
		$location.path('/overview/refresh').replace();
	else
		auth.signin({}, function(profile, token) {
			$log.debug(JSON.stringify(profile));
			$log.debug(token);

			$localStorage.profile = profile;
			$localStorage.token = token;

			var name = profile.username;
			var email = profile.email;
			var userID = profile.user_id;
			var avatar = profile.picture;

			dataService.getPlayerByExternalId(userID)
			.then(function(result) {
				$log.debug('LoginController: found player', JSON.stringify(result));
				dataService.setLoggedInPlayer(result);
				$timeout(function() {
					$location.path('/overview/refresh').replace();
				});
			}).catch(function(response) {
				$log.debug('LoginController: could not found player', JSON.stringify(response));
				var player = {
					name: name,
					email: email,
					externalID: userID,
					avatarURL: avatar
				};
				$log.debug('LoginController: try to register new player', JSON.stringify(player));

				$http.post(BACKEND_URL + '/player', player)
				.then(function(response) {
					$log.debug('LoginController: registered new player', JSON.stringify(response));
					var player = response.data;

					if (!player) {
						$scope.$apply(function() {
							toastr.error("There was an error - player \"" +
								name + "\" could not be registered. " +
								"Please try again in a couple of minutes.");
						});
						return;
					}

					$log.debug(player.key.id);

					dataService.setLoggedInPlayer(player);
					$timeout(function() {
						$location.path('/overview/refresh').replace();
					});
				}).catch(function(response) {
					$log.debug('LoginController: error when registering new player');
					$log.debug(JSON.stringify(response));

					dataService.setLoggedInPlayer(null);
					$scope.$apply(function() {
						toastr.error(response.message || "There was an error...");
						blockUI.stop();
					});
				});
			});
		}, function (err) {
			$log.debug("LoginController: error", JSON.stringify(err));
			dataService.setLoggedInPlayer(null);
			$scope.$apply(function() {
				toastr.error("There was an error...");
			});
		});
}); // LoginController
