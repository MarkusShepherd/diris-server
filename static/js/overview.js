dixitApp.controller('OverviewController', 
function($location, $log, $rootScope, $routeParams, $scope, blockUI, toastr, dataService) {

	var player = dataService.getLoggedInPlayer();

	if (!player) {
		$location.path('/login');
		return;
	}

	$scope.currentPlayer = player;
	$rootScope.menuItems = [];

	if (!blockUI.state().blocking)
		blockUI.start();

	var action = $routeParams.action;

	$rootScope.refreshPath = '/overview/refresh';
	$rootScope.refreshReload = action === 'refresh';

	dataService.getMatches(player.key.id, action === 'refresh', true)
	.then(function(matches) {
		$scope.$apply(function() {
			var status = {};
			$scope.matches = $.map(matches, function(match) {
				status[match.status] = true;
				return processMatch(match, player);
			});
			$scope.status = status;
			blockUI.stop();
		});
		$log.debug('Matches: ', $scope.matches);
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
		$scope.$apply(function() {
			toastr.error("There was an error fetching the data - please try again later...");
		});
	});

	dataService.getPlayers(action === 'refresh', true)
	.then(function(players) {
		$scope.$apply(function() {
			$scope.players = players;
		});
		$log.debug('Players: ', $scope.players);
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
	});

	$scope.newMatch = function() {
		$location.path('/newmatch');
	};

}); // PlayerController
