dixitApp.controller('ProfileController', 
function($location, $log, $rootScope, $routeParams, $scope, blockUI, dataService) {

	var player = dataService.getLoggedInPlayer();

	if (!player) {
		$location.path('/login');
		return;
	}

	$scope.currentPlayer = player;
	$rootScope.menuItems = [{
		link: '#/overview',
		label: 'Overview',
		glyphicon: 'home'
	}];

	if (!blockUI.state().blocking)
		blockUI.start();

	var pId = $routeParams.pId;
	var action = $routeParams.action;

	if (!pId)
		pId = player.key.id;

	if (!action)
		if (pId == player.key.id)
			action = 'edit';
		else
			action = 'view';

	$rootScope.refreshPath = null;
	$rootScope.refreshReload = false;

	dataService.getPlayer(pId)
	.then(function(player) {
		$scope.$apply(function() {
			$scope.player = player;
			blockUI.stop();
		});
		$log.debug('Player: ', $scope.player);
	}).catch(function(response) {
		$log.debug('error');
		$log.debug(response);
	});

}); // ProfileController
