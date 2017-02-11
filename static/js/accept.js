dixitApp.controller('AcceptController',
function($http, $location, $log, $rootScope, $routeParams, $scope, $timeout, blockUI, toastr, dataService, BACKEND_URL) {

	var player = dataService.getLoggedInPlayer();

	if (!player) {
		$location.path('/login');
		return;
	}

	if (!blockUI.state().blocking)
		blockUI.start();

	$scope.currentPlayer = player;
	$rootScope.menuItems = [{
		link: '#/overview',
		label: 'Overview',
		glyphicon: 'home'
	}];
	$rootScope.refreshPath = null;
	$rootScope.refreshReload = false;

	var mId = $routeParams.mId;
	$scope.mId = mId;

	dataService.getMatch(mId)
	.then(function(match) {
		$scope.$apply(function() {
			$scope.match = processMatch(match, player);
		});
		return $scope.match;
	}).then(function(match) {
		var promises = $.map(match.playerKeys, function(key) {
			return dataService.getPlayer(key.id);
		});
		$scope.players = {};
		Promise.all(promises)
		.then(function(players) {
			$scope.$apply(function() {
				$.each(players, function(i, player) {
					$scope.players[player.key.id] = player;
				});
				blockUI.stop();
			});
		});
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function() {
			toastr.error("There was an error fetching the data - please try again later...");
			blockUI.stop();
		});
	});

	$scope.accept = function() {
		$log.debug("Hit accept");

		$http.post(BACKEND_URL + '/match/' + mId + '/accept/' + player.key.id)
		.then(function(response) {
			$log.debug(response);
			$timeout(function() {
				$location.path('/overview/refresh');
			});
		}).catch(function(response) {
			$log.debug('error');
			$log.debug(response);
			$scope.$apply(function() {
				toastr.error("There was an error...");
			});
		});
	};
}); // AcceptController
